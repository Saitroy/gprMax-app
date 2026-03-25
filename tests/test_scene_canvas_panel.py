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
from gprmax_workbench.domain.models import MaterialDefinition, Vector3, default_project
from gprmax_workbench.domain.validation import validate_project
from gprmax_workbench.ui.widgets.model_editor.scene_canvas_panel import (
    SceneCanvasPanel,
    _SceneEntityItem,
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

    def test_scene_items_render_as_visual_entities(self) -> None:
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
            scene_items = [
                item for item in panel._scene.items() if isinstance(item, _SceneEntityItem)  # noqa: SLF001
            ]

            self.assertGreaterEqual(len(scene_items), 2)
            geometry_item = panel._entity_items[("geometry", 0)]  # noqa: SLF001
            receiver_item = panel._entity_items[("receiver", 0)]  # noqa: SLF001

            self.assertFalse(
                geometry_item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
            )
            self.assertTrue(
                receiver_item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
            )

    def test_scene_refresh_does_not_keep_deleted_qt_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            editor.add_receiver()
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._set_selected_row("receiver", 0)  # noqa: SLF001
            panel._refresh_scene()  # noqa: SLF001
            panel._set_selected_row("receiver", 0)  # noqa: SLF001

            self.assertEqual(panel._selected_entity_ref.kind, "receiver")  # noqa: SLF001

    def test_scene_clamps_positions_to_domain_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.domain.size_m.x = 1.0
            project.model.domain.size_m.y = 1.0
            project.model.domain.size_m.z = 0.2
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            receiver_index = editor.add_receiver()
            geometry_index = editor.add_geometry("box")
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            receiver_ref = None
            geometry_ref = None
            for row in range(panel._entity_list.count()):  # noqa: SLF001
                entity_ref = panel._entity_list.item(row).data(256)  # noqa: SLF001
                if entity_ref.kind == "receiver" and entity_ref.index == receiver_index:
                    receiver_ref = entity_ref
                if entity_ref.kind == "geometry" and entity_ref.index == geometry_index:
                    geometry_ref = entity_ref
            self.assertIsNotNone(receiver_ref)
            self.assertIsNotNone(geometry_ref)
            panel._apply_entity_position(  # noqa: SLF001
                receiver_ref,
                Vector3(5.0, -1.0, 7.0),
            )
            panel._apply_entity_position(  # noqa: SLF001
                geometry_ref,
                Vector3(5.0, 5.0, 5.0),
            )

            receiver = project.model.receivers[receiver_index]
            geometry = project.model.geometry[geometry_index]
            lower = geometry.parameters["lower_left_m"]
            upper = geometry.parameters["upper_right_m"]

            self.assertLessEqual(receiver.position_m.x, project.model.domain.size_m.x)
            self.assertGreaterEqual(receiver.position_m.y, 0.0)
            self.assertLessEqual(receiver.position_m.z, project.model.domain.size_m.z)
            self.assertGreaterEqual(lower["x"], 0.0)
            self.assertLessEqual(upper["x"], project.model.domain.size_m.x)
            self.assertGreaterEqual(lower["y"], 0.0)
            self.assertLessEqual(upper["y"], project.model.domain.size_m.y)

    def test_scene_domain_editor_updates_project_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._domain_x.setValue(2.5)  # noqa: SLF001
            panel._domain_y.setValue(1.7)  # noqa: SLF001
            panel._domain_z.setValue(0.3)  # noqa: SLF001
            panel._apply_domain_changes()  # noqa: SLF001

            self.assertAlmostEqual(project.model.domain.size_m.x, 2.5)
            self.assertAlmostEqual(project.model.domain.size_m.y, 1.7)
            self.assertAlmostEqual(project.model.domain.size_m.z, 0.3)

    def test_scene_receiver_inspector_updates_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            receiver_index = editor.add_receiver()
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._set_selected_row("receiver", receiver_index)  # noqa: SLF001
            panel._outputs_edit.setText("Ez, Hx")  # noqa: SLF001

            self.assertEqual(project.model.receivers[receiver_index].outputs, ["Ez", "Hx"])

    def test_geometry_color_depends_on_material_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001),
                MaterialDefinition(identifier="sand", relative_permittivity=3.0, conductivity=0.0005),
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            first_index = editor.add_geometry("box")
            second_index = editor.add_geometry("box")
            project.model.geometry[first_index].material_ids = ["soil"]
            project.model.geometry[second_index].material_ids = ["sand"]
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)

            first_color = panel._entity_items[("geometry", first_index)]._color.name()  # noqa: SLF001
            second_color = panel._entity_items[("geometry", second_index)]._color.name()  # noqa: SLF001

            self.assertNotEqual(first_color, second_color)
            self.assertIn("soil", panel._entity_items[("geometry", first_index)]._secondary_label)  # noqa: SLF001

    def test_resize_mode_shows_box_handles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001)
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            geometry_index = editor.add_geometry("box")
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
            panel._scene_mode_combo.setCurrentIndex(panel._scene_mode_combo.findData("resize"))  # noqa: SLF001

            roles = {handle.role for handle in panel._resize_handles}  # noqa: SLF001
            self.assertEqual(len(panel._resize_handles), 8)  # noqa: SLF001
            self.assertIn("corner_br", roles)
            self.assertIn("edge_right", roles)
            self.assertIn("edge_bottom", roles)

    def test_scene_toolbar_reflects_tool_mode_and_plane_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            panel = SceneCanvasPanel(LocalizationService("en"), editor, validation)

            panel.set_project(project)
            panel._scene_tool_combo.setCurrentIndex(panel._scene_tool_combo.findData("measure"))  # noqa: SLF001

            self.assertTrue(panel._tool_buttons["measure"].isChecked())  # noqa: SLF001
            self.assertFalse(panel._mode_buttons["resize"].isEnabled())  # noqa: SLF001

            panel._set_scene_tool_from_toolbar("select")  # noqa: SLF001
            panel._set_scene_mode_from_toolbar("resize")  # noqa: SLF001
            panel._set_plane_from_toolbar("yz")  # noqa: SLF001

            self.assertTrue(panel._tool_buttons["select"].isChecked())  # noqa: SLF001
            self.assertTrue(panel._mode_buttons["resize"].isChecked())  # noqa: SLF001
            self.assertTrue(panel._plane_buttons["yz"].isChecked())  # noqa: SLF001
            self.assertEqual(panel._plane, "yz")  # noqa: SLF001

    def test_create_tool_adds_selected_entity_at_click_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._scene_tool_combo.setCurrentIndex(panel._scene_tool_combo.findData("create"))  # noqa: SLF001
            panel._handle_palette_click("receiver")  # noqa: SLF001
            panel._handle_empty_scene_click(0.25, 0.35)  # noqa: SLF001

            self.assertEqual(len(project.model.receivers), 1)
            self.assertAlmostEqual(project.model.receivers[0].position_m.x, 0.25)
            self.assertAlmostEqual(project.model.receivers[0].position_m.y, 0.35)

    def test_measure_tool_creates_measurement_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._scene_tool_combo.setCurrentIndex(panel._scene_tool_combo.findData("measure"))  # noqa: SLF001
            panel._handle_empty_scene_click(0.1, 0.2)  # noqa: SLF001
            panel._handle_pointer_move(0.4, 0.6)  # noqa: SLF001

            self.assertGreaterEqual(len(panel._measurement_items), 2)  # noqa: SLF001
            self.assertGreaterEqual(len(panel._cursor_items), 4)  # noqa: SLF001
            self.assertIn("X=", panel._cursor_status_label.text())  # noqa: SLF001

    def test_cylinder_resize_mode_shows_endpoint_and_radius_handles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001)
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            geometry_index = editor.add_geometry("cylinder")
            panel = SceneCanvasPanel(LocalizationService("en"), editor, validation)

            panel.set_project(project)
            panel._set_plane_from_toolbar("xz")  # noqa: SLF001
            panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
            panel._scene_mode_combo.setCurrentIndex(panel._scene_mode_combo.findData("resize"))  # noqa: SLF001

            roles = {handle.role for handle in panel._resize_handles}  # noqa: SLF001

            self.assertEqual(roles, {"start", "end", "radius_pos", "radius_neg"})

    def test_resize_preview_does_not_commit_until_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.domain.size_m = Vector3(1.0, 1.0, 0.1)
            project.model.materials = [
                MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001)
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            geometry_index = editor.add_geometry("box")
            geometry = project.model.geometry[geometry_index]
            geometry.material_ids = ["soil"]
            geometry.parameters["lower_left_m"] = {"x": 0.4, "y": 0.4, "z": 0.02}
            geometry.parameters["upper_right_m"] = {"x": 0.6, "y": 0.6, "z": 0.08}
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
            panel._scene_mode_combo.setCurrentIndex(panel._scene_mode_combo.findData("resize"))  # noqa: SLF001
            panel._preview_geometry_resize("corner_br", panel._scene.sceneRect().bottomRight())  # noqa: SLF001

            lower_before = project.model.geometry[geometry_index].parameters["lower_left_m"]["x"]
            self.assertEqual(lower_before, 0.4)
            self.assertGreaterEqual(len(panel._preview_items), 2)  # noqa: SLF001

    def test_resize_handle_updates_box_size_within_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.domain.size_m = Vector3(1.0, 1.0, 0.1)
            project.model.materials = [
                MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001)
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            editor = ModelEditorService(state)
            validation = ValidationService(state)
            geometry_index = editor.add_geometry("box")
            geometry = project.model.geometry[geometry_index]
            geometry.material_ids = ["soil"]
            geometry.parameters["lower_left_m"] = {"x": 0.4, "y": 0.4, "z": 0.02}
            geometry.parameters["upper_right_m"] = {"x": 0.6, "y": 0.6, "z": 0.08}
            panel = SceneCanvasPanel(LocalizationService("ru"), editor, validation)

            panel.set_project(project)
            panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
            panel._scene_mode_combo.setCurrentIndex(panel._scene_mode_combo.findData("resize"))  # noqa: SLF001
            panel._resize_geometry_from_handle_release("corner_br", panel._scene.sceneRect().bottomRight())  # noqa: SLF001

            updated = project.model.geometry[geometry_index]
            lower = updated.parameters["lower_left_m"]
            upper = updated.parameters["upper_right_m"]
            self.assertAlmostEqual(lower["x"], 0.0, places=6)
            self.assertAlmostEqual(lower["y"], 0.0, places=6)
            self.assertAlmostEqual(upper["x"], 1.0, places=6)
            self.assertAlmostEqual(upper["y"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
