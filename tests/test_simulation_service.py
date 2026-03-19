from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

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
    def __init__(self) -> None:
        self.started = False

    def start(self, command, *, working_directory, callbacks):
        self.started = True
        callbacks.on_stdout("stdout line\n")
        callbacks.on_stderr("stderr line\n")
        callbacks.on_completed(0, False)
        return _FakeProcess()


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


if __name__ == "__main__":
    unittest.main()
