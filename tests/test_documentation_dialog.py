from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.ui.dialogs.documentation_dialog import DocumentationDialog
from gprmax_workbench.ui.views.welcome_view import ExampleProjectItem


class DocumentationDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_dialog_sets_examples_and_translates_title(self) -> None:
        dialog = DocumentationDialog(
            localization=LocalizationService("ru"),
            repo_root=Path.cwd(),
        )

        dialog.set_examples(
            [
                ExampleProjectItem(
                    title="Cylinder A-scan",
                    description="Demo",
                    path="D:/demo/project",
                )
            ]
        )
        dialog.retranslate_ui()

        self.assertTrue(dialog.windowTitle())
        self.assertEqual(dialog._examples_actions.count(), 1)


if __name__ == "__main__":
    unittest.main()
