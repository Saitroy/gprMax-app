from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.ui.views.welcome_view import WelcomeView


class WelcomeViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_dashboard_reflows_to_one_column_at_compact_width(self) -> None:
        view = WelcomeView(LocalizationService("en"))
        view.resize(1100, 760)
        view.show()
        self._app.processEvents()

        wide_status_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._status_card)  # noqa: SLF001
        )
        self.assertEqual(wide_status_position[:2], (0, 1))

        view.resize(900, 700)
        self._app.processEvents()

        compact_status_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._status_card)  # noqa: SLF001
        )
        self.assertEqual(compact_status_position[:2], (1, 0))


if __name__ == "__main__":
    unittest.main()
