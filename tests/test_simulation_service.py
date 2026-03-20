from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.input_generation_service import InputGenerationService
from gprmax_workbench.application.services.simulation_service import (
    SimulationRuntimeCapabilityError,
    SimulationService,
)
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.capability_status import CapabilityLevel, CapabilityStatus
from gprmax_workbench.domain.engine_config import EngineConfig, EngineMode
from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.domain.runtime_info import RuntimeInfo
from gprmax_workbench.domain.models import default_project
from gprmax_workbench.domain.simulation import SimulationRunRecord
from gprmax_workbench.infrastructure.gprmax.adapter import GprMaxExecutionRequest
from gprmax_workbench.infrastructure.gprmax.input_generator import GprMaxInputGenerator
from gprmax_workbench.infrastructure.persistence.artifact_store import RunArtifactStore
from gprmax_workbench.infrastructure.persistence.run_repository import RunRepository


class _FakeAdapter:
    def build_command(self, request: GprMaxExecutionRequest) -> list[str]:
        return ["python", "-m", "gprMax", str(request.input_file)]

    def describe_runtime(self) -> str:
        return "python -m gprMax"

    def runtime_config(self):
        return None

    def probe_runtime(self, timeout_seconds: float = 5.0):
        return True, "ok"


class _FakeProcess:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class _FakeRunner:
    def __init__(self, *, batch_output_count: int = 0) -> None:
        self.started = False
        self._batch_output_count = batch_output_count

    def start(self, command, *, working_directory, callbacks):
        self.started = True
        if self._batch_output_count > 0:
            output_directory = Path(working_directory) / "input" / "output"
            output_directory.mkdir(parents=True, exist_ok=True)
            for index in range(1, self._batch_output_count + 1):
                (output_directory / f"simulation{index}.out").write_text(
                    f"trace {index}",
                    encoding="utf-8",
                )
        callbacks.on_stdout("stdout line\n")
        callbacks.on_stderr("stderr line\n")
        callbacks.on_completed(0, False)
        return _FakeProcess()


class _MergeCapableAdapter(_FakeAdapter):
    def __init__(self, python_executable: str) -> None:
        self._python_executable = python_executable

    def runtime_config(self):
        class _RuntimeConfig:
            def __init__(self, python_executable: str) -> None:
                self.python_executable = python_executable

        return _RuntimeConfig(self._python_executable)


class SimulationServiceTests(unittest.TestCase):
    def test_start_run_creates_artifacts_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Stage 3 Demo", Path(temp_dir))
            state = AppState(current_project=project)
            runtime_info = RuntimeInfo(
                engine=EngineConfig(
                    mode=EngineMode.BUNDLED,
                    python_executable=Path("python"),
                ),
                app_version="test",
                bundled_engine_version="test",
                gprmax_version="test",
                settings_path=Path(temp_dir) / "settings.json",
                logs_directory=Path(temp_dir) / "logs",
                cache_directory=Path(temp_dir) / "cache",
                temp_directory=Path(temp_dir) / "temp",
                capabilities=[
                    CapabilityStatus(code="cpu", level=CapabilityLevel.READY),
                    CapabilityStatus(code="gpu", level=CapabilityLevel.OPTIONAL),
                    CapabilityStatus(code="mpi", level=CapabilityLevel.OPTIONAL),
                ],
                is_healthy=True,
            )
            service = SimulationService(
                adapter=_FakeAdapter(),
                input_generation_service=InputGenerationService(
                    generator=GprMaxInputGenerator(),
                    artifact_store=RunArtifactStore(),
                ),
                artifact_store=RunArtifactStore(),
                run_repository=RunRepository(),
                runner=_FakeRunner(),
                state=state,
                runtime_info_provider=lambda: runtime_info,
            )

            run_record = service.start_simulation(project, SimulationRunConfig())

            self.assertEqual(run_record.status, SimulationStatus.COMPLETED)
            self.assertTrue(run_record.input_file.exists())
            self.assertTrue(run_record.metadata_path.exists())
            self.assertEqual(len(state.run_history), 1)
            snapshot = service.get_log_snapshot_for_run(run_record)
            self.assertIn("stdout line", snapshot.combined_text)
            self.assertIn("stderr line", snapshot.combined_text)

    def test_rejects_gpu_run_when_runtime_capability_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("GPU Demo", Path(temp_dir))
            state = AppState(current_project=project)
            runner = _FakeRunner()
            runtime_info = RuntimeInfo(
                engine=EngineConfig(
                    mode=EngineMode.BUNDLED,
                    python_executable=Path("python"),
                ),
                app_version="test",
                bundled_engine_version="test",
                gprmax_version="test",
                settings_path=Path(temp_dir) / "settings.json",
                logs_directory=Path(temp_dir) / "logs",
                cache_directory=Path(temp_dir) / "cache",
                temp_directory=Path(temp_dir) / "temp",
                capabilities=[
                    CapabilityStatus(code="cpu", level=CapabilityLevel.READY),
                    CapabilityStatus(
                        code="gpu",
                        level=CapabilityLevel.OPTIONAL,
                        detail="pycuda is not available in the current runtime.",
                    ),
                    CapabilityStatus(code="mpi", level=CapabilityLevel.OPTIONAL),
                ],
                is_healthy=True,
            )
            service = SimulationService(
                adapter=_FakeAdapter(),
                input_generation_service=InputGenerationService(
                    generator=GprMaxInputGenerator(),
                    artifact_store=RunArtifactStore(),
                ),
                artifact_store=RunArtifactStore(),
                run_repository=RunRepository(),
                runner=runner,
                state=state,
                runtime_info_provider=lambda: runtime_info,
            )

            with self.assertRaises(SimulationRuntimeCapabilityError):
                service.start_simulation(
                    project,
                    SimulationRunConfig(use_gpu=True),
                )

            self.assertFalse(runner.started)
            self.assertEqual(state.run_history, [])

    def test_merges_batch_outputs_after_successful_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Batch Demo", Path(temp_dir))
            state = AppState(current_project=project)
            runner = _FakeRunner(batch_output_count=3)
            service = SimulationService(
                adapter=_MergeCapableAdapter(sys.executable),
                input_generation_service=InputGenerationService(
                    generator=GprMaxInputGenerator(),
                    artifact_store=RunArtifactStore(),
                ),
                artifact_store=RunArtifactStore(),
                run_repository=RunRepository(),
                runner=runner,
                state=state,
            )

            def _fake_merge(command, cwd, capture_output, text, check, timeout):
                self.assertEqual(command[0], sys.executable)
                self.assertEqual(command[1:3], ["-m", "tools.outputfiles_merge"])
                basefilename = Path(command[3])
                (basefilename.parent / f"{basefilename.name}_merged.out").write_text(
                    "merged",
                    encoding="utf-8",
                )

                class _Completed:
                    returncode = 0
                    stdout = "merged ok\n"
                    stderr = ""

                return _Completed()

            with patch(
                "gprmax_workbench.application.services.simulation_service.subprocess.run",
                side_effect=_fake_merge,
            ) as merge_run:
                run_record = service.start_simulation(
                    project,
                    SimulationRunConfig(num_model_runs=3),
                )

            self.assertTrue(merge_run.called)
            self.assertTrue(
                any(path.endswith("simulation_merged.out") for path in run_record.output_files)
            )
            snapshot = service.get_log_snapshot_for_run(run_record)
            self.assertIn("merged ok", snapshot.stdout_text)

    def test_suggests_batch_run_count_from_history_for_stepped_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Stepped Demo", Path(temp_dir))
            project.advanced_input_overrides = [
                "#src_steps: 0.002 0 0",
                "#rx_steps: 0.002 0 0",
            ]
            state = AppState(current_project=project)
            run_repository = RunRepository()
            historical_record = _build_historical_record(project.root, num_model_runs=60)
            run_repository.save(historical_record)
            service = SimulationService(
                adapter=_FakeAdapter(),
                input_generation_service=InputGenerationService(
                    generator=GprMaxInputGenerator(),
                    artifact_store=RunArtifactStore(),
                ),
                artifact_store=RunArtifactStore(),
                run_repository=run_repository,
                runner=_FakeRunner(),
                state=state,
            )

            suggested = service.suggest_run_configuration(project, SimulationRunConfig())

            self.assertEqual(suggested.num_model_runs, 60)


def _build_historical_record(
    project_root: Path,
    *,
    num_model_runs: int,
) -> SimulationRunRecord:
    run_id = "historical-bscan"
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
        status=SimulationStatus.COMPLETED,
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
        exit_code=0,
        finished_at=datetime(2026, 3, 19, tzinfo=UTC),
    )


if __name__ == "__main__":
    unittest.main()
