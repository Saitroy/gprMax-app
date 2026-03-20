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
from gprmax_workbench.domain.models import (
    AntennaModelDefinition,
    GeometryImportDefinition,
    Vector3,
    default_project,
)
from gprmax_workbench.domain.validation import validate_project
from gprmax_workbench.ui.widgets.model_editor.libraries_panel import LibrariesPanel


class LibrariesPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_previews_show_import_command_and_antenna_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Libraries Demo", Path(temp_dir))
            project.model.geometry_imports = [
                GeometryImportDefinition(
                    identifier="import_1",
                    position_m=Vector3(0.1, 0.2, 0.0),
                    geometry_hdf5="assets/object.h5",
                    materials_file="assets/materials.txt",
                    dielectric_smoothing=True,
                )
            ]
            project.model.antenna_models = [
                AntennaModelDefinition(
                    identifier="ant_1",
                    library="gprmax_user_libs",
                    model_key="gssi_1500",
                    module_path="user_libs.antennas.GSSI",
                    function_name="antenna_like_GSSI_1500",
                    position_m=Vector3(0.12, 0.09, 0.1),
                    resolution_m=0.002,
                )
            ]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            panel = LibrariesPanel(
                LocalizationService("en"),
                ModelEditorService(state),
                ValidationService(state),
            )

            panel.set_project(project)
            panel._tabs.setCurrentIndex(0)  # noqa: SLF001
            self.assertIn("#geometry_objects_read:", panel._import_preview_label.text())  # noqa: SLF001
            panel._tabs.setCurrentIndex(1)  # noqa: SLF001
            panel._antennas_list.setCurrentRow(0)  # noqa: SLF001
            self.assertIn("from user_libs.antennas.GSSI import antenna_like_GSSI_1500", panel._antenna_preview_label.text())  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
