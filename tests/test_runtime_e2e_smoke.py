from __future__ import annotations

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.diagnostics_service import DiagnosticsService
from gprmax_workbench.application.services.engine_resolution_service import EngineResolutionService
from gprmax_workbench.application.services.input_generation_service import InputGenerationService
from gprmax_workbench.application.services.runtime_service import RuntimeService
from gprmax_workbench.application.services.settings_service import SettingsService
from gprmax_workbench.application.services.simulation_service import SimulationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.infrastructure.gprmax.adapter import SubprocessGprMaxAdapter
from gprmax_workbench.infrastructure.gprmax.input_generator import GprMaxInputGenerator
from gprmax_workbench.infrastructure.gprmax.runner import GprMaxSubprocessRunner
from gprmax_workbench.infrastructure.persistence.artifact_store import RunArtifactStore
from gprmax_workbench.infrastructure.persistence.run_repository import RunRepository
from gprmax_workbench.infrastructure.project_store import JsonProjectStore
from gprmax_workbench.infrastructure.results.hdf5_reader import Hdf5ResultsReader
from gprmax_workbench.infrastructure.runtime.bundled_runtime import BundledRuntimeProvider
from gprmax_workbench.infrastructure.runtime.diagnostics import RuntimeDiagnostics
from gprmax_workbench.infrastructure.runtime.engine_locator import EngineLocator
from gprmax_workbench.infrastructure.runtime.external_runtime import ExternalRuntimeProvider
from gprmax_workbench.infrastructure.runtime.path_manager import PathManager
from gprmax_workbench.infrastructure.runtime.versioning import VersioningService
from gprmax_workbench.infrastructure.settings import SettingsManager


class RuntimeE2ESmokeTests(unittest.TestCase):
    def test_bundled_engine_completes_ascan_example_and_results_are_readable(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        example_root = repo_root / "examples" / "cylinder_ascan_2d"
        bundled_python = repo_root / "engine" / "python" / "Scripts" / "python.exe"

        if not example_root.exists():
            self.skipTest("Example project is not available.")
        if not bundled_python.exists():
            self.skipTest("Bundled runtime is not available in this checkout.")
        try:
            import h5py  # noqa: F401
        except ImportError:
            self.skipTest("h5py is not available in the test environment.")

        tmp_root = repo_root / ".tmp"
        tmp_root.mkdir(exist_ok=True)

        with tempfile.TemporaryDirectory(dir=tmp_root) as temp_dir:
            run_root = Path(temp_dir)
            project_root = run_root / "project"
            project_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                example_root / "project.gprwb.json",
                project_root / "project.gprwb.json",
            )

            settings_manager = SettingsManager(
                app_name="gprmax_workbench_e2e",
                base_dir=run_root / "app-settings",
            )
            settings_service = SettingsService(settings_manager)
            path_manager = PathManager(
                settings_manager=settings_manager,
                installation_root=repo_root,
            )
            adapter = SubprocessGprMaxAdapter()
            runtime_service = RuntimeService(
                settings_service=settings_service,
                engine_resolution_service=EngineResolutionService(
                    EngineLocator(
                        bundled_provider=BundledRuntimeProvider(path_manager),
                        external_provider=ExternalRuntimeProvider(),
                    )
                ),
                diagnostics_service=DiagnosticsService(
                    RuntimeDiagnostics(
                        path_manager=path_manager,
                        versioning=VersioningService(),
                    )
                ),
                adapter=adapter,
            )
            runtime_info = runtime_service.refresh()

            self.assertTrue(runtime_info.is_healthy, runtime_info.diagnostics)
            self.assertEqual(runtime_info.engine.mode.value, "bundled")

            project = JsonProjectStore().load(project_root)
            repository = RunRepository()
            artifact_store = RunArtifactStore()
            state = AppState(current_project=project)
            simulation_service = SimulationService(
                adapter=adapter,
                input_generation_service=InputGenerationService(
                    generator=GprMaxInputGenerator(),
                    artifact_store=artifact_store,
                ),
                artifact_store=artifact_store,
                run_repository=repository,
                runner=GprMaxSubprocessRunner(),
                state=state,
                runtime_info_provider=runtime_service.runtime_info,
            )

            configuration = simulation_service.suggest_run_configuration(
                project,
                SimulationRunConfig(),
            )
            readiness = simulation_service.assess_run_readiness(project, configuration)

            self.assertTrue(
                readiness.is_ready,
                readiness.blocking_messages
                + readiness.warning_messages
                + readiness.runtime_messages,
            )

            run_record = simulation_service.start_simulation(project, configuration)
            deadline = time.monotonic() + 180
            while True:
                current = simulation_service.get_run_status()
                self.assertIsNotNone(current)
                if current.status not in {SimulationStatus.PREPARING, SimulationStatus.RUNNING}:
                    run_record = current
                    break
                if time.monotonic() >= deadline:
                    simulation_service.cancel_simulation()
                    self.fail("Bundled runtime smoke run timed out.")
                time.sleep(0.2)

            loaded = repository.load(run_record.metadata_path)
            self.assertEqual(loaded.status, SimulationStatus.COMPLETED)
            self.assertTrue(loaded.runtime is not None)
            self.assertTrue(loaded.input_sha256)
            self.assertTrue(loaded.output_files)

            output_file = next(
                (
                    loaded.working_directory / relative_path
                    for relative_path in loaded.output_files
                    if relative_path.endswith(".out")
                ),
                None,
            )
            self.assertIsNotNone(output_file)
            assert output_file is not None
            self.assertTrue(output_file.exists())

            reader = Hdf5ResultsReader()
            metadata = reader.load_metadata(output_file)
            receivers = reader.list_receivers(output_file)

            self.assertEqual(metadata.receiver_count, 1)
            self.assertTrue(receivers)
            self.assertTrue(reader.list_components(output_file, receivers[0].receiver_id))


if __name__ == "__main__":
    unittest.main()
