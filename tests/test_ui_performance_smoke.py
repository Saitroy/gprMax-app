from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.application.services.model_editor_service import ModelEditorService
from gprmax_workbench.application.services.validation_service import ValidationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.models import MaterialDefinition, default_project
from gprmax_workbench.domain.validation import validate_project
from gprmax_workbench.ui.widgets.model_editor.scene_canvas_panel import SceneCanvasPanel


def test_large_scene_inspector_preview_stays_lightweight(tmp_path: Path) -> None:
    QApplication.instance() or QApplication([])
    project = default_project("Large scene", tmp_path)
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
    geometry_index = editor.add_geometry("box")
    for _index in range(300):
        editor.add_receiver()
    panel = SceneCanvasPanel(LocalizationService("en"), editor, ValidationService(state))
    panel.set_project(project)
    panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001

    started = time.perf_counter()
    panel._size_x.setValue(0.45)  # noqa: SLF001
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert elapsed_ms < 35
    assert len(panel._preview_items) >= 1  # noqa: SLF001
