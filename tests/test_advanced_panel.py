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
from gprmax_workbench.infrastructure.gprmax.command_registry import GprMaxCommandRegistry
from gprmax_workbench.ui.widgets.model_editor.advanced_panel import AdvancedPanel


class AdvancedPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_block_lists_follow_project_state_and_move_raw_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Advanced Demo", Path(temp_dir))
            project.advanced_input_overrides = ["#title: Demo", "#messages: y"]
            project.model.python_blocks = ["print('a')", "print('b')"]
            state = AppState(
                current_project=project,
                current_project_validation=validate_project(project),
            )
            panel = AdvancedPanel(
                LocalizationService("en"),
                ModelEditorService(state),
                ValidationService(state),
                GprMaxCommandRegistry(),
            )

            panel.set_project(project)
            self.assertEqual(panel._raw_blocks_list.count(), 2)  # noqa: SLF001
            self.assertEqual(panel._python_blocks_list.count(), 2)  # noqa: SLF001

            panel._raw_blocks_list.setCurrentRow(1)  # noqa: SLF001
            panel._move_raw_block(-1)  # noqa: SLF001

            self.assertTrue(panel._raw_editor.toPlainText().splitlines()[0].startswith("#messages"))  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
