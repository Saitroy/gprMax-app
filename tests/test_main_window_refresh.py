from __future__ import annotations

import os
import sys
import unittest
from types import SimpleNamespace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.app import ApplicationContext
from gprmax_workbench.application.services.input_generation_service import InputGenerationService
from gprmax_workbench.application.services.input_preview_service import InputPreviewService
from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.application.services.model_editor_service import ModelEditorService
from gprmax_workbench.application.services.validation_service import ValidationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.engine_config import EngineConfig, EngineMode
from gprmax_workbench.domain.runtime_info import RuntimeInfo
from gprmax_workbench.domain.viewer_state import ResultsViewerState
from gprmax_workbench.infrastructure.gprmax.command_registry import GprMaxCommandRegistry
from gprmax_workbench.infrastructure.gprmax.input_generator import GprMaxInputGenerator
from gprmax_workbench.infrastructure.persistence.artifact_store import RunArtifactStore
from gprmax_workbench.infrastructure.settings import AppSettings
from gprmax_workbench.ui.main_window import MainWindow
from gprmax_workbench.ui.theme import apply_theme


class _SettingsServiceStub:
    def __init__(self) -> None:
        self.settings = AppSettings()

    def ui_state_value(self, _key: str, default=None):
        return default

    def update_ui_state(self, _key: str, _value: object | None) -> AppSettings:
        return self.settings

    def recent_projects(self):
        return []


class _RuntimeServiceStub:
    def __init__(self) -> None:
        engine = EngineConfig(
            mode=EngineMode.EXTERNAL,
            python_executable=Path(sys.executable),
            source_label="Test runtime",
        )
        self._runtime_info = RuntimeInfo(
            engine=engine,
            app_version="test",
            bundled_engine_version=None,
            gprmax_version="test",
            settings_path=Path("settings.json"),
            logs_directory=Path("logs"),
            cache_directory=Path("cache"),
            temp_directory=Path("temp"),
            is_healthy=True,
        )

    def runtime_info(self) -> RuntimeInfo:
        return self._runtime_info

    def refresh(self) -> RuntimeInfo:
        return self._runtime_info


class _WorkspaceServiceStub:
    def __init__(self, state: AppState) -> None:
        self.state = state

    def current_project_file(self):
        return None


class _SimulationServiceStub:
    def runtime_label(self) -> str:
        return "Test runtime"

    def get_run_status(self):
        return None

    def get_log_snapshot_for_run(self, _run):
        return []

    def assess_run_readiness(self, _configuration):
        return SimpleNamespace(can_run=False, errors=[], warnings=[])


class _ResultsServiceStub:
    viewer_state = ResultsViewerState()

    def refresh_results(self, _project_root):
        return []

    def focus_run(self, run_id: str | None) -> None:
        self.viewer_state.selected_run_id = run_id


class _TraceServiceStub:
    def list_output_components(self, _output_path, _receiver_id):
        return []


class _BscanServiceStub:
    def load_bscan_if_available(self, *_args, **_kwargs):
        return None


class MainWindowRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])
        apply_theme(cls._app)

    def test_sidebar_uses_collapsible_readable_navigation_drawer(self) -> None:
        state = AppState()
        validation_service = ValidationService(state)
        input_generation_service = InputGenerationService(
            GprMaxInputGenerator(),
            RunArtifactStore(),
        )
        context = ApplicationContext(
            settings_manager=object(),
            settings_service=_SettingsServiceStub(),
            localization_service=LocalizationService("en"),
            runtime_service=_RuntimeServiceStub(),
            project_store=object(),
            project_service=object(),
            gprmax_adapter=object(),
            model_editor_service=ModelEditorService(state),
            validation_service=validation_service,
            input_generation_service=input_generation_service,
            input_preview_service=InputPreviewService(
                input_generation_service,
                validation_service,
            ),
            command_registry=GprMaxCommandRegistry(),
            simulation_service=_SimulationServiceStub(),
            run_service=object(),
            results_service=_ResultsServiceStub(),
            trace_service=_TraceServiceStub(),
            bscan_service=_BscanServiceStub(),
            state=state,
            workspace_service=_WorkspaceServiceStub(state),
        )
        window = MainWindow(context)

        self.addCleanup(window._simulation_refresh_timer.stop)  # noqa: SLF001
        self.addCleanup(window.deleteLater)
        window.show()
        self._app.processEvents()

        self.assertEqual(window._sidebar.maximumWidth(), 104)  # noqa: SLF001
        self.assertEqual(window._sidebar.minimumWidth(), 104)  # noqa: SLF001
        self.assertTrue(window._navigation.isHidden())  # noqa: SLF001
        self.assertTrue(window._rail_settings_button.isHidden())  # noqa: SLF001
        self.assertTrue(window._rail_documentation_button.isHidden())  # noqa: SLF001
        self.assertEqual(window._navigation_toggle_button.text(), "← Menu")  # noqa: SLF001
        self.assertGreater(window._navigation_animation.duration(), 0)  # noqa: SLF001
        self.assertEqual(  # noqa: SLF001
            window._navigation.verticalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.assertEqual(  # noqa: SLF001
            window._navigation.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.assertTrue(  # noqa: SLF001
            window._sidebar_subtitle.isHidden()
            or not window._sidebar_subtitle.isVisible()
        )
        self.assertEqual(window._sidebar_width_for_window(1440), 196)  # noqa: SLF001
        self.assertTrue(  # noqa: SLF001
            window._sidebar_status_area.isHidden()
            or not window._sidebar_status_area.isVisible()
        )
        width_before_expand = window.width()
        expected_expanded_width = window._sidebar_width_for_window(window.width())  # noqa: SLF001
        window._set_navigation_expanded(True, animated=False)  # noqa: SLF001
        self._app.processEvents()

        self.assertFalse(window._navigation.isHidden())  # noqa: SLF001
        self.assertEqual(window._sidebar.maximumWidth(), expected_expanded_width)  # noqa: SLF001
        self.assertGreaterEqual(window.width(), width_before_expand)
        self.assertEqual(  # noqa: SLF001
            [
                window._navigation.item(index).text()
                for index in range(window._navigation.count())
            ],
            ["Welcome", "Model Editor", "Simulation", "Results"],
        )
        self.assertFalse(window._rail_settings_button.isHidden())  # noqa: SLF001
        self.assertFalse(window._rail_documentation_button.isHidden())  # noqa: SLF001
        self.assertEqual(window._rail_settings_button.text(), "Settings")  # noqa: SLF001
        self.assertEqual(  # noqa: SLF001
            window._rail_documentation_button.text(),
            "Documentation",
        )
        self.assertTrue(window._rail_settings_button.toolTip())  # noqa: SLF001
        self.assertTrue(window._rail_documentation_button.toolTip())  # noqa: SLF001
        rail_actions: list[str] = []
        window._rail_settings_button.clicked.disconnect()  # noqa: SLF001
        window._rail_documentation_button.clicked.disconnect()  # noqa: SLF001
        window._rail_settings_button.clicked.connect(lambda: rail_actions.append("settings"))  # noqa: SLF001
        window._rail_documentation_button.clicked.connect(lambda: rail_actions.append("docs"))  # noqa: SLF001
        window._rail_settings_button.click()  # noqa: SLF001
        window._rail_documentation_button.click()  # noqa: SLF001
        self.assertEqual(rail_actions, ["settings", "docs"])

        self.assertEqual(window._navigation.count(), len(window._pages))  # noqa: SLF001
        window._navigation.setCurrentRow(2)  # noqa: SLF001
        self._app.processEvents()

        self.assertEqual(window._stack.currentIndex(), 2)  # noqa: SLF001

        window._set_navigation_expanded(False, animated=False)  # noqa: SLF001
        self._app.processEvents()

        self.assertTrue(window._navigation.isHidden())  # noqa: SLF001
        self.assertEqual(window._sidebar.maximumWidth(), 104)  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
