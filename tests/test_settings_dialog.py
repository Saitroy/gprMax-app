from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.ui.dialogs.settings_dialog import SettingsDialog
from gprmax_workbench.ui.views.settings_view import SettingsView


class SettingsDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_dialog_sets_title_and_hosts_settings_view(self) -> None:
        view = SettingsView(LocalizationService("ru"))
        dialog = SettingsDialog(view)

        dialog.retranslate_ui("Настройки")

        self.assertEqual(dialog.windowTitle(), "Настройки")
        self.assertIs(view.parentWidget(), dialog)


if __name__ == "__main__":
    unittest.main()
