from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.application.services.model_editor_service import ModelEditorService
from gprmax_workbench.application.services.validation_service import ValidationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.models import MaterialDefinition, default_project
from gprmax_workbench.domain.validation import validate_project
from gprmax_workbench.ui.widgets.model_editor.scene_canvas_panel import (
    SceneCanvasPanel,
    _AnchorItem,
)


class SceneCanvasPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_apply_entity_changes_updates_geometry_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(
                    identifier="soil",
                    relative_permittivity=4.0,
                    conductivity=0.001,
                )
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            geometry_index = editor.add_geometry("box")
            panel = SceneCanvasPanel(
                LocalizationService("ru"),
                editor,
                validation,
            )

            panel.set_project(project)
            panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
            panel._pos_x.setValue(0.4)  # noqa: SLF001
            panel._pos_y.setValue(0.3)  # noqa: SLF001
            panel._pos_z.setValue(0.05)  # noqa: SLF001
            panel._apply_entity_changes()  # noqa: SLF001

            geometry = project.model.geometry[geometry_index]
            lower = geometry.parameters["lower_left_m"]
            upper = geometry.parameters["upper_right_m"]
            center_x = (lower["x"] + upper["x"]) / 2
            center_y = (lower["y"] + upper["y"]) / 2
            center_z = (lower["z"] + upper["z"]) / 2
            self.assertAlmostEqual(center_x, 0.4, places=6)
            self.assertAlmostEqual(center_y, 0.3, places=6)
            self.assertAlmostEqual(center_z, 0.05, places=6)

    def test_snap_to_grid_rounds_receiver_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            receiver_index = editor.add_receiver()
            panel = SceneCanvasPanel(
                LocalizationService("en"),
                editor,
                validation,
            )

            panel.set_project(project)
            panel._snap_to_grid.setChecked(True)  # noqa: SLF001
            panel._grid_step.setValue(0.05)  # noqa: SLF001
            panel._apply_entity_position(  # noqa: SLF001
                panel._entity_list.item(receiver_index).data(256),  # noqa: SLF001
                project.model.receivers[receiver_index].position_m,
            )
            panel._set_selected_row("receiver", receiver_index)  # noqa: SLF001
            panel._pos_x.setValue(0.213)  # noqa: SLF001
            panel._pos_y.setValue(0.287)  # noqa: SLF001
            panel._pos_z.setValue(0.041)  # noqa: SLF001
            panel._apply_entity_changes()  # noqa: SLF001

            receiver = project.model.receivers[receiver_index]
            self.assertAlmostEqual(receiver.position_m.x, 0.2, places=6)
            self.assertAlmostEqual(receiver.position_m.y, 0.3, places=6)
            self.assertAlmostEqual(receiver.position_m.z, 0.05, places=6)

    def test_anchor_items_ignore_view_transformations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(
                    identifier="soil",
                    relative_permittivity=4.0,
                    conductivity=0.001,
                )
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            editor.add_geometry("box")
            editor.add_receiver()
            panel = SceneCanvasPanel(
                LocalizationService("ru"),
                editor,
                validation,
            )

            panel.set_project(project)
            anchor_items = [
                item for item in panel._scene.items() if isinstance(item, _AnchorItem)  # noqa: SLF001
            ]

            self.assertGreaterEqual(len(anchor_items), 2)
            for item in anchor_items:
                self.assertTrue(
                    item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
                )


if __name__ == "__main__":
    unittest.main()
