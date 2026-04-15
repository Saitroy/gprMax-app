from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.input_generation_service import InputGenerationService
from gprmax_workbench.application.services.input_preview_service import InputPreviewService
from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.application.services.model_editor_service import ModelEditorService
from gprmax_workbench.application.services.validation_service import ValidationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.models import default_project
from gprmax_workbench.domain.validation import validate_project
from gprmax_workbench.infrastructure.gprmax.command_registry import GprMaxCommandRegistry
from gprmax_workbench.infrastructure.gprmax.input_generator import GprMaxInputGenerator
from gprmax_workbench.infrastructure.persistence.artifact_store import RunArtifactStore
from gprmax_workbench.ui.views.project_view import ProjectView


class ProjectViewSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def _build_view(self, temp_dir: str) -> ProjectView:
        project = default_project("Smoke", Path(temp_dir))
        state = AppState(
            current_project=project,
            current_project_validation=validate_project(project),
        )
        validation_service = ValidationService(state)
        model_editor_service = ModelEditorService(state)
        input_preview_service = InputPreviewService(
            InputGenerationService(GprMaxInputGenerator(), RunArtifactStore()),
            validation_service,
        )
        view = ProjectView(
            localization=LocalizationService("ru"),
            model_editor_service=model_editor_service,
            validation_service=validation_service,
            input_preview_service=input_preview_service,
            command_registry=GprMaxCommandRegistry(),
        )
        view.set_project(project, state.current_project_validation, False, None)
        return view

    def test_project_view_defaults_to_basic_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)
            localization = view._localization  # noqa: SLF001

            labels = [
                view._section_nav.item(index).text()  # noqa: SLF001
                for index in range(view._section_nav.count())  # noqa: SLF001
            ]

            self.assertIn(localization.text("project.section.scene"), labels)
            self.assertIn(localization.text("project.section.libraries"), labels)
            self.assertNotIn(localization.text("project.section.advanced"), labels)
            self.assertEqual(labels[0], localization.text("project.section.scene"))

    def test_project_view_can_enable_advanced_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)
            localization = view._localization  # noqa: SLF001

            view.set_advanced_mode(True)

            labels = [
                view._section_nav.item(index).text()  # noqa: SLF001
                for index in range(view._section_nav.count())  # noqa: SLF001
            ]

            self.assertIn(localization.text("project.section.advanced"), labels)

    def test_model_editor_toolbar_switches_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)
            localization = view._localization  # noqa: SLF001

            materials_button = view._section_buttons["project.section.materials"]  # noqa: SLF001
            materials_button.click()

            self.assertIs(view._section_stack.currentWidget(), view._materials_panel)  # noqa: SLF001
            self.assertTrue(materials_button.isChecked())
            self.assertEqual(
                materials_button.text(),
                localization.text("project.section.materials"),
            )
            self.assertFalse(view._nav_card.isVisible())  # noqa: SLF001

    def test_scene_edit_request_switches_to_matching_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)

            view._scene_panel.edit_requested.emit("receiver")  # noqa: SLF001

            self.assertIs(view._section_stack.currentWidget(), view._receivers_panel)  # noqa: SLF001

    def test_standard_desktop_width_keeps_project_splitter_horizontal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)
            view.resize(1040, 720)
            view.show()
            self._app.processEvents()

            self.assertEqual(view._content_splitter.orientation(), Qt.Orientation.Horizontal)  # noqa: SLF001
            self.assertGreaterEqual(view._content_splitter.handleWidth(), 10)  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
