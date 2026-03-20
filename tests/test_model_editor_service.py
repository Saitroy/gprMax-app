from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.model_editor_service import ModelEditorService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.models import (
    AntennaModelDefinition,
    GeometryImportDefinition,
    MaterialDefinition,
    Vector3,
    default_project,
)
from gprmax_workbench.domain.validation import validate_project


class ModelEditorServiceTests(unittest.TestCase):
    def test_add_and_update_material_marks_project_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Editor Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            service = ModelEditorService(state)

            index = service.add_material()
            validation = service.update_material(
                index,
                MaterialDefinition(
                    identifier="soil",
                    relative_permittivity=4.0,
                    conductivity=0.001,
                ),
            )

            self.assertTrue(state.current_project_dirty)
            self.assertEqual(project.model.materials[0].identifier, "soil")
            self.assertIs(state.current_project_validation, validation)

    def test_update_project_overview_updates_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Editor Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            service = ModelEditorService(state)

            service.update_project_overview(
                project_name="Updated Project",
                description="Model editor test",
                model_title="Updated Model",
                model_notes="Notes",
                model_tags=["lab", "demo"],
                domain_size_m=Vector3(2.0, 1.5, 0.2),
                resolution_m=Vector3(0.01, 0.01, 0.01),
                time_window_s=4e-9,
                scan_trace_count=60,
            )

            self.assertEqual(project.metadata.name, "Updated Project")
            self.assertEqual(project.model.title, "Updated Model")
            self.assertEqual(project.model.domain.size_m.x, 2.0)
            self.assertEqual(project.model.tags, ["lab", "demo"])
            self.assertEqual(project.model.scan_trace_count, 60)

    def test_available_material_ids_deduplicates_builtin_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Editor Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(
                    identifier="water",
                    relative_permittivity=81.0,
                    conductivity=0.1,
                )
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            service = ModelEditorService(state)

            material_ids = service.available_material_ids()

            self.assertEqual(material_ids.count("water"), 1)

    def test_add_update_and_delete_geometry_import(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Editor Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            service = ModelEditorService(state)

            index = service.add_geometry_import()
            validation = service.update_geometry_import(
                index,
                GeometryImportDefinition(
                    identifier="import_1",
                    position_m=Vector3(0.0, 0.0, 0.0),
                    geometry_hdf5="assets/object.h5",
                    materials_file="assets/materials.txt",
                    dielectric_smoothing=True,
                ),
            )
            next_index = service.delete_geometry_import(index)

            self.assertTrue(validation.is_valid)
            self.assertEqual(project.model.geometry_imports, [])
            self.assertIsNone(next_index)

    def test_add_update_antenna_and_advanced_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Editor Demo", Path(temp_dir))
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            service = ModelEditorService(state)

            antenna_index = service.add_antenna_model()
            service.update_antenna_model(
                antenna_index,
                AntennaModelDefinition(
                    identifier="ant_1",
                    library="gprmax_user_libs",
                    model_key="gssi_1500",
                    module_path="user_libs.antennas.GSSI",
                    function_name="antenna_like_GSSI_1500",
                    position_m=Vector3(0.1, 0.1, 0.02),
                    resolution_m=0.002,
                ),
            )
            service.update_advanced_workspace(
                python_blocks=["print('hello')", ""],
                raw_input_overrides=["#src_steps: 0.002 0 0", ""],
            )

            self.assertEqual(project.model.antenna_models[0].identifier, "ant_1")
            self.assertEqual(project.model.python_blocks, ["print('hello')"])
            self.assertEqual(project.advanced_input_overrides, ["#src_steps: 0.002 0 0"])


if __name__ == "__main__":
    unittest.main()
