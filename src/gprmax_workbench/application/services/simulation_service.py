from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from ...domain.execution_status import SimulationStatus
from ...domain.gprmax_config import SimulationRunConfig
from ...domain.models import Project
from ...domain.simulation import (
    PreparedSimulationRun,
    RunArtifacts,
    SimulationLogSnapshot,
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
    ) -> None:
        self._adapter = adapter
        self._input_generation_service = input_generation_service
        self._artifact_store = artifact_store
        self._run_repository = run_repository
        self._runner = runner
        self._state = state
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
        )
        return PreparedSimulationRun(
            record=record,
            input_text=preview.text,
            preview_text=preview.text,
            validation_messages=preview.warnings,
        )

    def export_input(
        self,
        project: Project,
        configuration: SimulationRunConfig,
        destination: Path | None = None,
    ) -> Path:
        return self._input_generation_service.export_preview(
            project=project,
            configuration=configuration,
            destination=destination,
        )

    def validate_before_run(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> ValidationResult:
        return self._input_generation_service.validate_before_run(project, configuration)

    def prepare_simulation_run(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> PreparedSimulationRun:
        validation = self.validate_before_run(project, configuration)
        if not validation.is_valid:
            raise SimulationPreparationError(validation)

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
            validation_messages=generated.warnings,
        )

    def start_simulation(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> SimulationRunRecord:
        with self._lock:
            if self._state.active_run is not None and self._state.active_run.status in {
                SimulationStatus.PREPARING,
                SimulationStatus.RUNNING,
            }:
                raise RuntimeError("A simulation run is already active.")

        runtime_ok, runtime_message = self.runtime_probe()
        if not runtime_ok:
            raise RuntimeError(runtime_message)

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
            record.status = SimulationStatus.FAILED
            record.finished_at = datetime.now(tz=UTC)
            record.error_summary = str(exc)
            self._run_repository.save(record)
            with self._lock:
                self._state.active_run = record
                self._state.run_history = self._merge_history(record)
            raise RuntimeError(str(exc)) from exc

        with self._lock:
            self._active_process = process
            self._state.active_run = record
            self._state.run_history = self._merge_history(record)

        return record

    def cancel_simulation(self) -> bool:
        with self._lock:
            process = self._active_process
        if process is None:
            return False
        process.cancel()
        return True

    def get_run_status(self) -> SimulationRunRecord | None:
        with self._lock:
            return self._state.active_run

    def get_run_history(self, project_root: Path | None) -> list[SimulationRunRecord]:
        if project_root is None:
            return []
        history = self._run_repository.load_history(project_root)
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
        )

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
        record.output_files = self._artifact_store.list_output_files(artifacts)

        if cancelled:
            record.status = SimulationStatus.CANCELLED
        elif exit_code == 0:
            record.status = SimulationStatus.COMPLETED
        else:
            record.status = SimulationStatus.FAILED
            log_snapshot = self.get_log_snapshot(run_id)
            record.error_summary = self._derive_error_summary(log_snapshot.stderr_text)

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

    def _read_text_file(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")


class SimulationPreparationError(ValueError):
    def __init__(self, validation: ValidationResult) -> None:
        self.validation = validation
        message = "; ".join(
            f"{issue.path}: {issue.message}" for issue in validation.errors
        )
        super().__init__(message or "Simulation preparation failed.")
