from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from collections import namedtuple
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.input_generation_service import InputGenerationService
from gprmax_workbench.application.services.simulation_service import (
    SimulationReadinessError,
    SimulationService,
)
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.capability_status import CapabilityLevel, CapabilityStatus
from gprmax_workbench.domain.engine_config import EngineConfig, EngineMode
from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import GprMaxRuntimeConfig, SimulationRunConfig
from gprmax_workbench.domain.models import default_project
from gprmax_workbench.domain.runtime_info import RuntimeInfo
from gprmax_workbench.domain.simulation import SimulationRunRecord
from gprmax_workbench.infrastructure.gprmax.adapter import GprMaxExecutionRequest
from gprmax_workbench.infrastructure.gprmax.input_generator import GprMaxInputGenerator
from gprmax_workbench.infrastructure.persistence.artifact_store import RunArtifactStore
from gprmax_workbench.infrastructure.persistence.run_repository import RunRepository


class _FakeAdapter:
    def __init__(
        self,
        *,
        runtime_config: GprMaxRuntimeConfig | None = None,
        runtime_ok: bool = True,
        runtime_message: str | None = None,
        label: str | None = None,
    ) -> None:
        self._runtime_config = runtime_config or GprMaxRuntimeConfig(
            python_executable=sys.executable,
            module_name="gprMax",
        )
        self._label = label or (
            f"{self._runtime_config.python_executable} -m {self._runtime_config.module_name}"
        )
        self._runtime_ok = runtime_ok
        self._runtime_message = runtime_message or self._label

    def build_command(self, request: GprMaxExecutionRequest) -> list[str]:
        return [
            self._runtime_config.python_executable,
            "-m",
            self._runtime_config.module_name,
            str(request.input_file),
        ]

    def describe_runtime(self) -> str:
        return self._label

    def runtime_config(self) -> GprMaxRuntimeConfig:
        return self._runtime_config

    def probe_runtime(self, timeout_seconds: float = 5.0) -> tuple[bool, str]:
        return self._runtime_ok, self._runtime_message


class _FakeProcess:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class _DeferredRunner:
    def __init__(
        self,
        *,
        start_exception: Exception | None = None,
        start_hook=None,
    ) -> None:
        self.started = False
        self.process = _FakeProcess()
        self.callbacks = None
        self.command: list[str] = []
        self.working_directory: Path | None = None
        self._start_exception = start_exception
        self._start_hook = start_hook

    def start(self, command, *, working_directory, callbacks):
        self.started = True
        self.command = list(command)
        self.working_directory = Path(working_directory)
        self.callbacks = callbacks
        if self._start_exception is not None:
            raise self._start_exception
        if self._start_hook is not None:
            self._start_hook(self.working_directory)
        return self.process

    def emit_stdout(self, chunk: str = "stdout line\n") -> None:
        if self.callbacks is None:
            raise AssertionError("Runner callbacks are not available.")
        self.callbacks.on_stdout(chunk)

    def emit_stderr(self, chunk: str = "stderr line\n") -> None:
        if self.callbacks is None:
            raise AssertionError("Runner callbacks are not available.")
        self.callbacks.on_stderr(chunk)

    def complete(self, *, exit_code: int, cancelled: bool = False) -> None:
        if self.callbacks is None:
            raise AssertionError("Runner callbacks are not available.")
        self.callbacks.on_completed(exit_code, cancelled)


class SimulationServiceTests(unittest.TestCase):
    def test_start_run_persists_snapshot_metadata_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Stage 3 Demo", Path(temp_dir))
            runner = _DeferredRunner()
            runtime_info = self._runtime_info(temp_dir, diagnostics=["Bundled engine ready."])
            service, state, repository = self._create_service(
                project,
                runner=runner,
                runtime_info=runtime_info,
            )

            run_record = service.start_simulation(project, SimulationRunConfig())
            runner.emit_stdout()
            runner.emit_stderr()
            runner.complete(exit_code=0)

            loaded = repository.load(run_record.metadata_path)
            input_text = run_record.input_file.read_text(encoding="utf-8")

            self.assertEqual(loaded.status, SimulationStatus.COMPLETED)
            self.assertEqual(loaded.command, runner.command)
            self.assertIsNotNone(loaded.runtime)
            self.assertEqual(loaded.runtime.python_executable, sys.executable)
            self.assertEqual(loaded.runtime.module_name, "gprMax")
            self.assertEqual(loaded.runtime_label, service.runtime_label())
            self.assertIn("Bundled engine ready.", loaded.preflight_messages)
            self.assertEqual(
                loaded.input_sha256,
                hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
            )
            self.assertEqual(len(state.run_history), 1)

            snapshot = service.get_log_snapshot_for_run(run_record)
            self.assertIn("stdout line", snapshot.combined_text)
            self.assertIn("stderr line", snapshot.combined_text)

    def test_broken_runtime_blocks_prepare_and_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Broken Runtime Demo", Path(temp_dir))
            runner = _DeferredRunner()
            service, _, _ = self._create_service(
                project,
                runner=runner,
                adapter=_FakeAdapter(
                    runtime_ok=False,
                    runtime_message="Timed out while checking the gprMax runtime.",
                ),
                runtime_info=self._runtime_info(
                    temp_dir,
                    healthy=False,
                    diagnostics=["Bundled engine is unavailable."],
                ),
            )

            readiness = service.assess_run_readiness(project, SimulationRunConfig())

            self.assertFalse(readiness.is_ready)
            self.assertIn(
                "Timed out while checking the gprMax runtime.",
                readiness.blocking_messages,
            )
            self.assertIn(
                "The base gprMax runtime is not healthy.",
                readiness.blocking_messages,
            )

            with self.assertRaises(SimulationReadinessError) as start_error:
                service.start_simulation(project, SimulationRunConfig())
            with self.assertRaises(SimulationReadinessError):
                service.prepare_simulation_run(project, SimulationRunConfig())

            self.assertIn(
                "Timed out while checking the gprMax runtime.",
                start_error.exception.report.blocking_messages,
            )
            self.assertFalse(runner.started)

    def test_rejects_gpu_run_when_runtime_capability_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("GPU Demo", Path(temp_dir))
            runner = _DeferredRunner()
            runtime_info = self._runtime_info(
                temp_dir,
                capabilities=[
                    CapabilityStatus(code="cpu", level=CapabilityLevel.READY),
                    CapabilityStatus(
                        code="gpu",
                        level=CapabilityLevel.OPTIONAL,
                        detail="pycuda is not available in the current runtime.",
                    ),
                    CapabilityStatus(code="mpi", level=CapabilityLevel.OPTIONAL),
                ],
            )
            service, state, _ = self._create_service(
                project,
                runner=runner,
                runtime_info=runtime_info,
            )

            with self.assertRaises(SimulationReadinessError) as exc:
                service.start_simulation(project, SimulationRunConfig(use_gpu=True))

            self.assertIn(
                "GPU execution is not available in the current runtime.",
                exc.exception.report.blocking_messages[0],
            )
            self.assertFalse(runner.started)
            self.assertEqual(state.run_history, [])

    def test_assess_run_readiness_warns_on_low_disk_space(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Disk Demo", Path(temp_dir))
            service, _, _ = self._create_service(project)
            disk_usage = namedtuple("disk_usage", "total used free")

            with patch(
                "gprmax_workbench.application.services.simulation_service.shutil.disk_usage",
                return_value=disk_usage(total=10, used=5, free=1024),
            ):
                readiness = service.assess_run_readiness(project, SimulationRunConfig())

            self.assertTrue(readiness.is_ready)
            self.assertTrue(
                any("Free disk space is very low" in message for message in readiness.warning_messages)
            )

    def test_cancel_flow_marks_run_as_cancelled_after_completion_callback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Cancel Demo", Path(temp_dir))
            runner = _DeferredRunner()
            service, state, repository = self._create_service(project, runner=runner)

            run_record = service.start_simulation(project, SimulationRunConfig())

            self.assertTrue(service.cancel_simulation())
            self.assertTrue(runner.process.cancelled)

            runner.complete(exit_code=1, cancelled=True)
            loaded = repository.load(run_record.metadata_path)

            self.assertEqual(state.active_run.status, SimulationStatus.CANCELLED)
            self.assertEqual(loaded.status, SimulationStatus.CANCELLED)
            self.assertEqual(loaded.error_summary, "Run cancelled by user.")

    def test_get_run_history_recovers_stale_running_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Recovery Demo", Path(temp_dir))
            repository = RunRepository()
            stale_record = _build_historical_record(
                project.root,
                run_id="stale-run",
                status=SimulationStatus.RUNNING,
                num_model_runs=1,
            )
            repository.save(stale_record)
            service, state, _ = self._create_service(
                project,
                run_repository=repository,
            )

            history = service.get_run_history(project.root)

            self.assertEqual(history[0].status, SimulationStatus.FAILED)
            self.assertIn("stale", history[0].error_summary.lower())
            self.assertEqual(state.run_history[0].status, SimulationStatus.FAILED)

    def test_start_failure_resets_run_state_and_persists_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Immediate Failure Demo", Path(temp_dir))
            runner = _DeferredRunner(start_exception=FileNotFoundError("python missing"))
            service, state, repository = self._create_service(project, runner=runner)

            with self.assertRaises(RuntimeError):
                service.start_simulation(project, SimulationRunConfig())

            self.assertTrue(state.run_history)
            failed_record = state.run_history[0]
            loaded = repository.load(failed_record.metadata_path)
            self.assertEqual(failed_record.status, SimulationStatus.FAILED)
            self.assertEqual(loaded.error_summary, "python missing")

    def test_successful_run_can_finish_without_output_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Missing Output Demo", Path(temp_dir))
            runner = _DeferredRunner()
            service, state, repository = self._create_service(project, runner=runner)

            run_record = service.start_simulation(project, SimulationRunConfig())
            runner.complete(exit_code=0)
            loaded = repository.load(run_record.metadata_path)

            self.assertEqual(state.active_run.status, SimulationStatus.COMPLETED)
            self.assertEqual(loaded.status, SimulationStatus.COMPLETED)
            self.assertEqual(loaded.output_files, [])

    def test_run_completion_survives_failed_output_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Merge Failure Demo", Path(temp_dir))
            runner = _DeferredRunner(start_hook=lambda workdir: _write_batch_outputs(workdir, 3))
            service, state, repository = self._create_service(project, runner=runner)

            run_record = service.start_simulation(
                project,
                SimulationRunConfig(num_model_runs=3),
            )

            class _Completed:
                returncode = 2
                stdout = ""
                stderr = "merge failed\n"

            with patch(
                "gprmax_workbench.application.services.simulation_service.subprocess.run",
                return_value=_Completed(),
            ):
                runner.complete(exit_code=0)

            loaded = repository.load(run_record.metadata_path)
            snapshot = service.get_log_snapshot_for_run(run_record)
            self.assertEqual(state.active_run.status, SimulationStatus.COMPLETED)
            self.assertEqual(loaded.status, SimulationStatus.COMPLETED)
            self.assertIn("merge failed", snapshot.stderr_text)
            self.assertTrue(any(path.endswith("simulation1.out") for path in loaded.output_files))

    def test_run_completion_survives_output_merge_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Merge Timeout Demo", Path(temp_dir))
            runner = _DeferredRunner(start_hook=lambda workdir: _write_batch_outputs(workdir, 2))
            service, state, repository = self._create_service(project, runner=runner)

            run_record = service.start_simulation(
                project,
                SimulationRunConfig(num_model_runs=2),
            )

            with patch(
                "gprmax_workbench.application.services.simulation_service.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="merge", timeout=120),
            ):
                runner.complete(exit_code=0)

            loaded = repository.load(run_record.metadata_path)
            self.assertEqual(state.active_run.status, SimulationStatus.COMPLETED)
            self.assertEqual(loaded.status, SimulationStatus.COMPLETED)
            self.assertFalse(any(path.endswith("_merged.out") for path in loaded.output_files))
            self.assertTrue(any(path.endswith("simulation1.out") for path in loaded.output_files))

    def test_suggests_batch_run_count_from_history_for_stepped_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Stepped Demo", Path(temp_dir))
            project.advanced_input_overrides = [
                "#src_steps: 0.002 0 0",
                "#rx_steps: 0.002 0 0",
            ]
            repository = RunRepository()
            repository.save(
                _build_historical_record(
                    project.root,
                    run_id="historical-bscan",
                    status=SimulationStatus.COMPLETED,
                    num_model_runs=60,
                )
            )
            service, _, _ = self._create_service(
                project,
                run_repository=repository,
            )

            suggested = service.suggest_run_configuration(project, SimulationRunConfig())

            self.assertEqual(suggested.num_model_runs, 60)

    def test_explicit_project_trace_count_overrides_history_and_current_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Stepped Demo", Path(temp_dir))
            project.advanced_input_overrides = [
                "#src_steps: 0.002 0 0",
                "#rx_steps: 0.002 0 0",
            ]
            project.model.scan_trace_count = 80
            repository = RunRepository()
            repository.save(
                _build_historical_record(
                    project.root,
                    run_id="historical-bscan",
                    status=SimulationStatus.COMPLETED,
                    num_model_runs=60,
                )
            )
            service, _, _ = self._create_service(
                project,
                run_repository=repository,
            )

            suggested = service.suggest_run_configuration(
                project,
                SimulationRunConfig(num_model_runs=5),
            )

            self.assertEqual(suggested.num_model_runs, 80)

    def _create_service(
        self,
        project,
        *,
        adapter: _FakeAdapter | None = None,
        runner: _DeferredRunner | None = None,
        run_repository: RunRepository | None = None,
        runtime_info: RuntimeInfo | None = None,
    ) -> tuple[SimulationService, AppState, RunRepository]:
        state = AppState(current_project=project)
        repository = run_repository or RunRepository()
        service = SimulationService(
            adapter=adapter or _FakeAdapter(),
            input_generation_service=InputGenerationService(
                generator=GprMaxInputGenerator(),
                artifact_store=RunArtifactStore(),
            ),
            artifact_store=RunArtifactStore(),
            run_repository=repository,
            runner=runner or _DeferredRunner(),
            state=state,
            runtime_info_provider=(lambda: runtime_info) if runtime_info is not None else None,
        )
        return service, state, repository

    def _runtime_info(
        self,
        temp_dir: str,
        *,
        healthy: bool = True,
        diagnostics: list[str] | None = None,
        capabilities: list[CapabilityStatus] | None = None,
    ) -> RuntimeInfo:
        return RuntimeInfo(
            engine=EngineConfig(
                mode=EngineMode.BUNDLED,
                python_executable=Path(sys.executable),
            ),
            app_version="test",
            bundled_engine_version="test",
            gprmax_version="test",
            settings_path=Path(temp_dir) / "settings.json",
            logs_directory=Path(temp_dir) / "logs",
            cache_directory=Path(temp_dir) / "cache",
            temp_directory=Path(temp_dir) / "temp",
            capabilities=capabilities
            or [
                CapabilityStatus(code="cpu", level=CapabilityLevel.READY),
                CapabilityStatus(code="gpu", level=CapabilityLevel.OPTIONAL),
                CapabilityStatus(code="mpi", level=CapabilityLevel.OPTIONAL),
            ],
            diagnostics=list(diagnostics or []),
            is_healthy=healthy,
        )


def _build_historical_record(
    project_root: Path,
    *,
    run_id: str,
    status: SimulationStatus,
    num_model_runs: int,
) -> SimulationRunRecord:
    run_dir = project_root / "runs" / run_id
    input_dir = run_dir / "input"
    output_dir = input_dir / "output"
    logs_dir = run_dir / "logs"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "simulation.in").write_text("#title: historical\n", encoding="utf-8")
    for index in range(1, 4):
        (output_dir / f"simulation{index}.out").write_text("", encoding="utf-8")

    return SimulationRunRecord(
        run_id=run_id,
        project_root=project_root,
        project_name="Historical",
        status=status,
        created_at=datetime(2026, 3, 19, tzinfo=UTC),
        working_directory=run_dir,
        input_file=input_dir / "simulation.in",
        output_directory=output_dir,
        stdout_log_path=logs_dir / "stdout.log",
        stderr_log_path=logs_dir / "stderr.log",
        combined_log_path=logs_dir / "combined.log",
        metadata_path=run_dir / "metadata.json",
        configuration=SimulationRunConfig(num_model_runs=num_model_runs),
        output_files=[f"input\\output\\simulation{index}.out" for index in range(1, 4)],
        exit_code=0 if status == SimulationStatus.COMPLETED else None,
        started_at=datetime(2026, 3, 19, tzinfo=UTC),
        finished_at=(
            datetime(2026, 3, 19, tzinfo=UTC)
            if status == SimulationStatus.COMPLETED
            else None
        ),
    )


def _write_batch_outputs(working_directory: Path, count: int) -> None:
    output_directory = working_directory / "input" / "output"
    output_directory.mkdir(parents=True, exist_ok=True)
    for index in range(1, count + 1):
        (output_directory / f"simulation{index}.out").write_text(
            f"trace {index}",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
