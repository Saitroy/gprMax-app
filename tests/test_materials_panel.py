from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.application.services.model_editor_service import ModelEditorService
from gprmax_workbench.application.services.validation_service import ValidationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.models import default_project
from gprmax_workbench.domain.validation import validate_project
from gprmax_workbench.ui.widgets.model_editor.materials_panel import MaterialsPanel


class MaterialsPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def _build_panel(self, temp_dir: str) -> tuple[MaterialsPanel, ModelEditorService]:
        project = default_project("Materials Demo", Path(temp_dir))
        state = AppState(
            current_project=project,
            current_project_validation=validate_project(project),
        )
        editor = ModelEditorService(state)
        validation = ValidationService(state)
        panel = MaterialsPanel(LocalizationService("en"), editor, validation)
        panel.set_project(project)
        return panel, editor

    def test_preset_creates_visual_material_card_for_empty_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            panel, editor = self._build_panel(temp_dir)

            panel._preset_buttons["wet_soil"].click()  # noqa: SLF001

            project = editor.current_project()
            self.assertIsNotNone(project)
            self.assertEqual(len(project.model.materials), 1)
            self.assertEqual(project.model.materials[0].identifier, "wet_soil")
            self.assertEqual(panel._list.count(), 1)  # noqa: SLF001
            self.assertIn("wet_soil", panel._preview_summary.text())  # noqa: SLF001
            self.assertIn("Used by scene objects: 0", panel._usage_label.text())  # noqa: SLF001

    def test_preset_replaces_selected_material_instead_of_adding_extra_cards(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            panel, editor = self._build_panel(temp_dir)

            panel._preset_buttons["dry_sand"].click()  # noqa: SLF001
            panel._preset_buttons["concrete"].click()  # noqa: SLF001

            project = editor.current_project()
            self.assertIsNotNone(project)
            self.assertEqual(len(project.model.materials), 1)
            self.assertEqual(project.model.materials[0].identifier, "concrete")
            self.assertEqual(panel._list.count(), 1)  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
