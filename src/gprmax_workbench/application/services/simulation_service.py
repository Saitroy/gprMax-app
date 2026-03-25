from __future__ import annotations

import hashlib
import logging
import shutil
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Callable
from uuid import uuid4

from ...domain.execution_status import SimulationStatus
from ...domain.gprmax_config import SimulationRunConfig
from ...domain.models import Project
from ...domain.project_introspection import project_scan_trace_count, project_uses_scan_steps
from ...domain.runtime_info import RuntimeInfo
from ...domain.simulation import (
    PreparedSimulationRun,
    RunArtifacts,
    SimulationLogSnapshot,
    SimulationReadinessReport,
    SimulationRunRecord,
)
from ...domain.validation import ValidationResult
from ...infrastructure.gprmax.adapter import GprMaxAdapter, GprMaxExecutionRequest
from ...infrastructure.gprmax.process_monitor import RunningProcess
from ...infrastructure.gprmax.runner import GprMaxSubprocessRunner, RunnerCallbacks
from ...infrastructure.persistence.artifact_store import RunArtifactStore
from ...infrastructure.persistence.run_repository import RunRepository
from ..state import AppState
from .input_generation_service import InputGenerationService

LOGGER = logging.getLogger(__name__)


class SimulationService:
    """Coordinates preparation, execution, log capture, and persistence of runs."""

    def __init__(
        self,
        *,
        adapter: GprMaxAdapter,
        input_generation_service: InputGenerationService,
        artifact_store: RunArtifactStore,
        run_repository: RunRepository,
        runner: GprMaxSubprocessRunner,
        state: AppState,
        runtime_info_provider: Callable[[], RuntimeInfo] | None = None,
    ) -> None:
        self._adapter = adapter
        self._input_generation_service = input_generation_service
        self._artifact_store = artifact_store
        self._run_repository = run_repository
        self._runner = runner
        self._state = state
        self._runtime_info_provider = runtime_info_provider
        self._lock = Lock()
        self._active_process: RunningProcess | None = None
        self._active_artifacts: RunArtifacts | None = None
        self._log_buffers: dict[str, dict[str, list[str]]] = {}

    def runtime_label(self) -> str:
        return self._adapter.describe_runtime()

    def runtime_probe(self) -> tuple[bool, str]:
        return self._adapter.probe_runtime()

    def rebuild_input_preview(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> PreparedSimulationRun:
        readiness = self.assess_run_readiness(project, configuration)
        configuration = readiness.configuration
        preview = self._input_generation_service.build_input_preview(
            project=project,
            configuration=configuration,
        )
        preview_path = self._artifact_store.write_preview(
            project_root=project.root,
            filename="preview.in",
            input_text=preview.text,
        )
        record = self._build_record(
            project=project,
            artifacts=RunArtifacts(
                run_directory=project.root / "generated",
                input_directory=preview_path.parent,
                output_directory=project.root / "generated" / "output",
                logs_directory=project.root / "generated",
                metadata_path=project.root / "generated" / "preview-metadata.json",
                input_file=preview_path,
                stdout_log_path=project.root / "generated" / "preview-stdout.log",
                stderr_log_path=project.root / "generated" / "preview-stderr.log",
                combined_log_path=project.root / "generated" / "preview-combined.log",
            ),
            configuration=configuration,
            status=SimulationStatus.PREPARING,
            input_text=preview.text,
            preflight_messages=(
                readiness.blocking_messages
                + readiness.warning_messages
                + readiness.runtime_messages
            ),
        )
        return PreparedSimulationRun(
            record=record,
            input_text=preview.text,
            preview_text=preview.text,
            validation_messages=readiness.blocking_messages
            + readiness.warning_messages
            + readiness.runtime_messages
            + preview.warnings,
        )

    def export_input(
        self,
        project: Project,
        configuration: SimulationRunConfig,
        destination: Path | None = None,
    ) -> Path:
        return self._input_generation_service.export_preview(
            project=project,
            configuration=self.suggest_run_configuration(project, configuration),
            destination=destination,
        )

    def validate_before_run(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> ValidationResult:
        effective_configuration = self.suggest_run_configuration(project, configuration)
        return self._input_generation_service.validate_before_run(
            project,
            effective_configuration,
        )

    def assess_run_readiness(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> SimulationReadinessReport:
        effective_configuration = self.suggest_run_configuration(project, configuration)
        validation = self.validate_before_run(project, effective_configuration)
        runtime_ok, runtime_message = self.runtime_probe()
        blocking_messages: list[str] = []
        warning_messages: list[str] = []
        runtime_messages: list[str] = []

        for issue in validation.warnings:
            warning_messages.append(f"{issue.path}: {issue.message}")

        if not runtime_ok and runtime_message:
            blocking_messages.append(runtime_message)

        if self._runtime_info_provider is not None:
            runtime_info = self._runtime_info_provider()
            if not runtime_info.is_healthy:
                blocking_messages.append("The base gprMax runtime is not healthy.")
            for diagnostic in runtime_info.diagnostics:
                if diagnostic:
                    runtime_messages.append(diagnostic)

        capability_message = self._execution_capability_message(effective_configuration)
        if capability_message:
            blocking_messages.append(capability_message)

        path_messages, path_warnings = self._path_and_disk_messages(project.root)
        blocking_messages.extend(path_messages)
        warning_messages.extend(path_warnings)

        with self._lock:
            active_run = self._state.active_run
            active_process = self._active_process
        is_busy = bool(
            active_run is not None
            and active_run.status in {SimulationStatus.PREPARING, SimulationStatus.RUNNING}
            and active_process is not None
        )
        if is_busy:
            blocking_messages.append("A simulation run is already active.")

        is_ready = (
            validation.is_valid
            and runtime_ok
            and not blocking_messages
        )
        return SimulationReadinessReport(
            configuration=effective_configuration,
            is_ready=is_ready,
            validation=validation,
            runtime_probe_ok=runtime_ok,
            runtime_probe_message=runtime_message,
            is_busy=is_busy,
            blocking_messages=blocking_messages,
            warning_messages=warning_messages,
            runtime_messages=runtime_messages,
        )

    def suggest_run_configuration(
        self,
        project: Project,
        configuration: SimulationRunConfig | None = None,
    ) -> SimulationRunConfig:
        effective_configuration = configuration or SimulationRunConfig()
        explicit_trace_count = project_scan_trace_count(project)
        if explicit_trace_count is not None:
            return replace(
                effective_configuration,
                num_model_runs=max(explicit_trace_count, 1),
            )
        if effective_configuration.num_model_runs > 1:
            return effective_configuration
        if not project_uses_scan_steps(project):
            return effective_configuration

        suggested_runs = self._suggest_num_model_runs(project)
        if suggested_runs <= 1:
            return effective_configuration
        return replace(effective_configuration, num_model_runs=suggested_runs)

    def prepare_simulation_run(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> PreparedSimulationRun:
        readiness = self.assess_run_readiness(project, configuration)
        configuration = readiness.configuration
        if not readiness.validation.is_valid:
            raise SimulationPreparationError(readiness.validation)
        if readiness.blocking_messages:
            raise SimulationReadinessError(readiness)

        artifacts = self._artifact_store.create_artifacts(
            project_root=project.root,
            run_id=self._new_run_id(),
        )
        generated = self._input_generation_service.build_input_preview(
            project=project,
            configuration=configuration,
        )
        self._artifact_store.write_input(artifacts, generated.text)

        record = self._build_record(
            project=project,
            artifacts=artifacts,
            configuration=configuration,
            status=SimulationStatus.PREPARING,
            input_text=generated.text,
            preflight_messages=readiness.warning_messages + readiness.runtime_messages,
        )
        self._run_repository.save(record)

        with self._lock:
            self._state.active_run = record
            self._state.run_history = self._merge_history(record)
            self._log_buffers[record.run_id] = {
                "combined": [],
                "stdout": [],
                "stderr": [],
            }
            self._active_artifacts = artifacts

        return PreparedSimulationRun(
            record=record,
            input_text=generated.text,
            preview_text=generated.text,
            validation_messages=readiness.warning_messages
            + readiness.runtime_messages
            + generated.warnings,
        )

    def start_simulation(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> SimulationRunRecord:
        stale_record: SimulationRunRecord | None = None
        with self._lock:
            active_run = self._state.active_run
            if active_run is not None and active_run.status in {
                SimulationStatus.PREPARING,
                SimulationStatus.RUNNING,
            }:
                if self._active_process is None:
                    stale_record = active_run
                else:
                    raise RuntimeError("A simulation run is already active.")

        if stale_record is not None:
            self._mark_run_as_stale(
                stale_record,
                reason=(
                    "A previous simulation run was left in a stale running state and has been reset."
                ),
            )

        readiness = self.assess_run_readiness(project, configuration)
        configuration = readiness.configuration
        if readiness.is_busy:
            raise SimulationReadinessError(readiness)
        if not readiness.validation.is_valid:
            raise SimulationPreparationError(readiness.validation)
        if readiness.blocking_messages:
            raise SimulationReadinessError(readiness)

        prepared = self.prepare_simulation_run(project, configuration)
        record = prepared.record
        command = self._adapter.build_command(
            GprMaxExecutionRequest(
                working_directory=record.working_directory,
                input_file=record.input_file,
                configuration=configuration,
            )
        )
        record.command = command
        record.started_at = datetime.now(tz=UTC)
        record.status = SimulationStatus.RUNNING
        self._run_repository.save(record)

        artifacts = self._active_artifacts
        if artifacts is None:
            raise RuntimeError("Run artifacts were not created.")

        try:
            process = self._runner.start(
                command=command,
                working_directory=record.working_directory,
                callbacks=RunnerCallbacks(
                    on_stdout=lambda chunk: self._handle_stdout(record.run_id, chunk),
                    on_stderr=lambda chunk: self._handle_stderr(record.run_id, chunk),
                    on_completed=lambda exit_code, cancelled: self._handle_completion(
                        record.run_id,
                        exit_code,
                        cancelled,
                    ),
                ),
            )
        except FileNotFoundError as exc:
            self._finalize_immediate_failure(record, str(exc))
            raise RuntimeError(str(exc)) from exc
        except Exception as exc:
            self._finalize_immediate_failure(record, str(exc))
            raise

        with self._lock:
            self._active_process = process
            self._state.active_run = record
            self._state.run_history = self._merge_history(record)

        return record

    def cancel_simulation(self) -> bool:
        with self._lock:
            process = self._active_process
            active_run = self._state.active_run
        if process is None:
            if active_run is not None and active_run.status in {
                SimulationStatus.PREPARING,
                SimulationStatus.RUNNING,
            }:
                self._mark_run_as_stale(
                    active_run,
                    reason=(
                        "The active simulation run had no live process attached and was reset."
                    ),
                )
            return False
        process.cancel()
        return True

    def get_run_status(self) -> SimulationRunRecord | None:
        with self._lock:
            return self._state.active_run

    def get_run_history(self, project_root: Path | None) -> list[SimulationRunRecord]:
        if project_root is None:
            return []
        history = self._recover_stale_history(project_root)
        with self._lock:
            self._state.run_history = history
        return history

    def get_log_snapshot(self, run_id: str | None = None) -> SimulationLogSnapshot:
        with self._lock:
            active_run = self._state.active_run
            target_run_id = run_id or (active_run.run_id if active_run else "")
            buffers = self._log_buffers.get(
                target_run_id,
                {"combined": [], "stdout": [], "stderr": []},
            )
            return SimulationLogSnapshot(
                run_id=target_run_id,
                combined_text="".join(buffers["combined"]),
                stdout_text="".join(buffers["stdout"]),
                stderr_text="".join(buffers["stderr"]),
            )

    def get_log_snapshot_for_run(
        self,
        run_record: SimulationRunRecord | None,
    ) -> SimulationLogSnapshot:
        if run_record is None:
            return SimulationLogSnapshot(
                run_id="",
                combined_text="",
                stdout_text="",
                stderr_text="",
            )

        with self._lock:
            active_run = self._state.active_run
            if active_run is not None and active_run.run_id == run_record.run_id:
                buffers = self._log_buffers.get(
                    run_record.run_id,
                    {"combined": [], "stdout": [], "stderr": []},
                )
                return SimulationLogSnapshot(
                    run_id=run_record.run_id,
                    combined_text="".join(buffers["combined"]),
                    stdout_text="".join(buffers["stdout"]),
                    stderr_text="".join(buffers["stderr"]),
                )

        return SimulationLogSnapshot(
            run_id=run_record.run_id,
            combined_text=self._read_text_file(run_record.combined_log_path),
            stdout_text=self._read_text_file(run_record.stdout_log_path),
            stderr_text=self._read_text_file(run_record.stderr_log_path),
        )

    def open_run_directory(self, run_record: SimulationRunRecord | None) -> Path | None:
        if run_record is None:
            return None
        return self._artifact_store.openable_directory(run_record.working_directory)

    def open_output_directory(self, run_record: SimulationRunRecord | None) -> Path | None:
        if run_record is None:
            return None
        return self._artifact_store.openable_directory(run_record.output_directory)

    def _build_record(
        self,
        *,
        project: Project,
        artifacts: RunArtifacts,
        configuration: SimulationRunConfig,
        status: SimulationStatus,
        input_text: str,
        preflight_messages: list[str] | None = None,
    ) -> SimulationRunRecord:
        return SimulationRunRecord(
            run_id=artifacts.run_directory.name,
            project_root=project.root,
            project_name=project.metadata.name,
            status=status,
            created_at=datetime.now(tz=UTC),
            working_directory=artifacts.run_directory,
            input_file=artifacts.input_file,
            output_directory=artifacts.output_directory,
            stdout_log_path=artifacts.stdout_log_path,
            stderr_log_path=artifacts.stderr_log_path,
            combined_log_path=artifacts.combined_log_path,
            metadata_path=artifacts.metadata_path,
            configuration=configuration,
            runtime=self._adapter.runtime_config(),
            runtime_label=self._adapter.describe_runtime(),
            preflight_messages=list(preflight_messages or []),
            input_sha256=self._hash_input_text(input_text),
        )

    def _hash_input_text(self, input_text: str) -> str:
        return hashlib.sha256(input_text.encode("utf-8")).hexdigest()

    def _execution_capability_message(
        self,
        configuration: SimulationRunConfig,
    ) -> str | None:
        if self._runtime_info_provider is None:
            return None

        runtime_info = self._runtime_info_provider()
        if configuration.use_gpu and not runtime_info.is_capability_ready("gpu"):
            return (
                "GPU execution is not available in the current runtime. "
                "Disable 'Use GPU' or install pycuda support in the bundled engine."
            )
        if configuration.mpi_tasks and not runtime_info.is_capability_ready("mpi"):
            return (
                "MPI execution is not available in the current runtime. "
                "Disable MPI or install mpi4py support in the bundled engine."
            )
        return None

    def _path_and_disk_messages(self, project_root: Path) -> tuple[list[str], list[str]]:
        blocking: list[str] = []
        warnings: list[str] = []
        for directory in (project_root, project_root / "runs", project_root / "generated"):
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                blocking.append(f"Path is not writable: {directory} ({exc})")

        try:
            free_space = shutil.disk_usage(project_root).free
        except OSError as exc:
            warnings.append(f"Could not inspect free disk space for {project_root}: {exc}")
        else:
            if free_space < 10 * 1024 * 1024:
                warnings.append(
                    f"Free disk space is very low in the project location: {free_space} bytes remaining."
                )

        return blocking, warnings

    def _finalize_immediate_failure(self, record: SimulationRunRecord, error_summary: str) -> None:
        record.status = SimulationStatus.FAILED
        record.finished_at = datetime.now(tz=UTC)
        record.error_summary = error_summary
        self._run_repository.save(record)
        with self._lock:
            self._active_process = None
            self._active_artifacts = None
            self._state.active_run = record
            self._state.run_history = self._merge_history(record)

    def _mark_run_as_stale(self, record: SimulationRunRecord, *, reason: str) -> SimulationRunRecord:
        record.status = SimulationStatus.FAILED
        record.finished_at = record.finished_at or datetime.now(tz=UTC)
        record.error_summary = reason
        self._run_repository.save(record)
        with self._lock:
            if self._state.active_run is not None and self._state.active_run.run_id == record.run_id:
                self._state.active_run = record
            self._active_process = None
            self._active_artifacts = None
            self._state.run_history = self._merge_history(record)
        return record

    def _recover_stale_history(self, project_root: Path) -> list[SimulationRunRecord]:
        history = self._run_repository.load_history(project_root)
        recovered: list[SimulationRunRecord] = []
        changed = False
        with self._lock:
            active_run_id = self._state.active_run.run_id if self._state.active_run is not None else None
            has_live_process = self._active_process is not None
        for record in history:
            if record.status not in {SimulationStatus.PREPARING, SimulationStatus.RUNNING}:
                recovered.append(record)
                continue
            if has_live_process and active_run_id == record.run_id:
                recovered.append(record)
                continue
            changed = True
            record.status = SimulationStatus.FAILED
            record.finished_at = record.finished_at or datetime.now(tz=UTC)
            record.error_summary = (
                "The run was recovered from a stale in-progress state because no live process was attached."
            )
            self._run_repository.save(record)
            recovered.append(record)
        if not changed:
            return history
        recovered.sort(key=lambda item: item.created_at, reverse=True)
        return recovered

    def _handle_stdout(self, run_id: str, chunk: str) -> None:
        with self._lock:
            buffers = self._log_buffers.get(run_id)
            active_run = self._state.active_run
            artifacts = self._active_artifacts
        if buffers is None or artifacts is None or active_run is None or active_run.run_id != run_id:
            return

        buffers["stdout"].append(chunk)
        buffers["combined"].append(f"[stdout] {chunk}")
        self._artifact_store.append_stdout(artifacts, chunk)

    def _handle_stderr(self, run_id: str, chunk: str) -> None:
        with self._lock:
            buffers = self._log_buffers.get(run_id)
            active_run = self._state.active_run
            artifacts = self._active_artifacts
        if buffers is None or artifacts is None or active_run is None or active_run.run_id != run_id:
            return

        buffers["stderr"].append(chunk)
        buffers["combined"].append(f"[stderr] {chunk}")
        self._artifact_store.append_stderr(artifacts, chunk)

    def _handle_completion(
        self,
        run_id: str,
        exit_code: int,
        cancelled: bool,
    ) -> None:
        with self._lock:
            record = self._state.active_run
            artifacts = self._active_artifacts
            self._active_process = None
        if record is None or artifacts is None or record.run_id != run_id:
            return

        record.finished_at = datetime.now(tz=UTC)
        record.exit_code = exit_code

        if cancelled:
            record.status = SimulationStatus.CANCELLED
            record.error_summary = "Run cancelled by user."
        elif exit_code == 0:
            record.status = SimulationStatus.COMPLETED
            self._maybe_merge_batch_outputs(record, artifacts)
        else:
            record.status = SimulationStatus.FAILED
            log_snapshot = self.get_log_snapshot(run_id)
            record.error_summary = self._derive_error_summary(log_snapshot.stderr_text)

        record.output_files = self._artifact_store.list_output_files(artifacts)
        self._run_repository.save(record)

        with self._lock:
            self._state.active_run = record
            self._state.run_history = self._merge_history(record)
            self._active_artifacts = None

        LOGGER.info("Run %s finished with status %s", record.run_id, record.status.value)

    def _derive_error_summary(self, stderr_text: str) -> str:
        stripped_lines = [line.strip() for line in stderr_text.splitlines() if line.strip()]
        if not stripped_lines:
            return "gprMax exited with a non-zero status code."
        return stripped_lines[-1]

    def _maybe_merge_batch_outputs(
        self,
        record: SimulationRunRecord,
        artifacts: RunArtifacts,
    ) -> None:
        if record.configuration.num_model_runs <= 1:
            return

        runtime = self._adapter.runtime_config()
        if runtime is None or not runtime.python_executable:
            LOGGER.warning(
                "Skipping output merge for run %s because runtime configuration is unavailable.",
                record.run_id,
            )
            return

        input_stem = record.input_file.stem
        candidate_directories = [
            record.input_file.parent / "output",
            record.output_directory,
        ]
        basefilename: Path | None = None
        for directory in candidate_directories:
            first_trace = directory / f"{input_stem}1.out"
            if first_trace.exists():
                basefilename = directory / input_stem
                break

        if basefilename is None:
            return

        merged_path = basefilename.parent / f"{basefilename.name}_merged.out"
        if merged_path.exists():
            return

        command = [
            runtime.python_executable,
            "-m",
            "tools.outputfiles_merge",
            str(basefilename),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=record.working_directory,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            LOGGER.warning("Failed to merge B-scan outputs for run %s: %s", record.run_id, exc)
            return

        if completed.stdout:
            self._append_merge_log(record.run_id, artifacts, "stdout", completed.stdout)
        if completed.stderr:
            self._append_merge_log(record.run_id, artifacts, "stderr", completed.stderr)

        if completed.returncode != 0:
            LOGGER.warning(
                "Output merge for run %s exited with code %s.",
                record.run_id,
                completed.returncode,
            )

    def _append_merge_log(
        self,
        run_id: str,
        artifacts: RunArtifacts,
        stream: str,
        chunk: str,
    ) -> None:
        with self._lock:
            buffers = self._log_buffers.get(run_id)
        if buffers is not None:
            buffers[stream].append(chunk)
            buffers["combined"].append(f"[{stream}] {chunk}")
        if stream == "stdout":
            self._artifact_store.append_stdout(artifacts, chunk)
            return
        self._artifact_store.append_stderr(artifacts, chunk)

    def _merge_history(self, current_record: SimulationRunRecord) -> list[SimulationRunRecord]:
        history = [
            item
            for item in self._run_repository.load_history(current_record.project_root)
            if item.run_id != current_record.run_id
        ]
        history.insert(0, current_record)
        return history

    def _new_run_id(self) -> str:
        return datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]

    def _suggest_num_model_runs(self, project: Project) -> int:
        for record in self._run_repository.load_history(project.root):
            if (
                record.status == SimulationStatus.COMPLETED
                and record.configuration.num_model_runs > 1
            ):
                return record.configuration.num_model_runs

            output_count = len(record.output_files)
            if record.status == SimulationStatus.COMPLETED and output_count > 1:
                return output_count
        return 1

    def _read_text_file(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _validate_execution_capabilities(
        self,
        configuration: SimulationRunConfig,
    ) -> None:
        message = self._execution_capability_message(configuration)
        if message is not None:
            raise SimulationRuntimeCapabilityError(message)


class SimulationPreparationError(ValueError):
    def __init__(self, validation: ValidationResult) -> None:
        self.validation = validation
        message = "; ".join(
            f"{issue.path}: {issue.message}" for issue in validation.errors
        )
        super().__init__(message or "Simulation preparation failed.")


class SimulationRuntimeCapabilityError(RuntimeError):
    """Raised when the selected run configuration requires unavailable runtime features."""


class SimulationReadinessError(RuntimeError):
    def __init__(self, report: SimulationReadinessReport) -> None:
        self.report = report
        message = "; ".join(report.blocking_messages)
        super().__init__(message or "Simulation is not ready to run.")
