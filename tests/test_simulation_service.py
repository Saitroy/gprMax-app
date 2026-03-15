from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.input_generation_service import InputGenerationService
from gprmax_workbench.application.services.simulation_service import SimulationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
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
    def start(self, command, *, working_directory, callbacks):
        callbacks.on_stdout("stdout line\n")
        callbacks.on_stderr("stderr line\n")
        callbacks.on_completed(0, False)
        return _FakeProcess()


class SimulationServiceTests(unittest.TestCase):
    def test_start_run_creates_artifacts_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Stage 3 Demo", Path(temp_dir))
            state = AppState(current_project=project)
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
            )

            run_record = service.start_simulation(project, SimulationRunConfig())

            self.assertEqual(run_record.status, SimulationStatus.COMPLETED)
            self.assertTrue(run_record.input_file.exists())
            self.assertTrue(run_record.metadata_path.exists())
            self.assertEqual(len(state.run_history), 1)
            snapshot = service.get_log_snapshot_for_run(run_record)
            self.assertIn("stdout line", snapshot.combined_text)
            self.assertIn("stderr line", snapshot.combined_text)


if __name__ == "__main__":
    unittest.main()
