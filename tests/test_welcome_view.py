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

    def test_home_prioritizes_actions_recent_projects_runtime_and_examples(self) -> None:
        view = WelcomeView(LocalizationService("en"))

        self.assertFalse(view._hero_card.isHidden())  # noqa: SLF001
        self.assertFalse(view._recent_card.isHidden())  # noqa: SLF001
        self.assertFalse(view._runtime_card.isHidden())  # noqa: SLF001
        self.assertFalse(view._examples_card.isHidden())  # noqa: SLF001
        self.assertTrue(view._status_card.isHidden())  # noqa: SLF001
        self.assertTrue(view._quick_start_card.isHidden())  # noqa: SLF001

    def test_home_wide_layout_places_recent_projects_beside_runtime_and_examples(self) -> None:
        view = WelcomeView(LocalizationService("en"))
        view.resize(1100, 760)
        view.show()
        self._app.processEvents()

        recent_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._recent_card)  # noqa: SLF001
        )
        runtime_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._runtime_card)  # noqa: SLF001
        )
        examples_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._examples_card)  # noqa: SLF001
        )
        self.assertEqual(recent_position[:4], (0, 0, 2, 1))
        self.assertEqual(runtime_position[:2], (0, 1))
        self.assertEqual(examples_position[:2], (1, 1))

    def test_home_compact_layout_stacks_recent_runtime_and_examples(self) -> None:
        view = WelcomeView(LocalizationService("en"))
        view.resize(900, 700)
        view.show()
        self._app.processEvents()

        recent_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._recent_card)  # noqa: SLF001
        )
        runtime_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._runtime_card)  # noqa: SLF001
        )
        examples_position = view._dashboard_grid.getItemPosition(  # noqa: SLF001
            view._dashboard_grid.indexOf(view._examples_card)  # noqa: SLF001
        )
        self.assertEqual(recent_position[:2], (0, 0))
        self.assertEqual(runtime_position[:2], (1, 0))
        self.assertEqual(examples_position[:2], (2, 0))


if __name__ == "__main__":
    unittest.main()
