from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.ui.views.simulation_view import SimulationView


class SimulationViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_hides_gpu_controls_and_returns_cpu_only_configuration(self) -> None:
        view = SimulationView(
            localization=LocalizationService("en"),
            runtime_label="Bundled runtime",
        )

        self.assertIsNone(view.findChild(QWidget, "simulation.gpu_checkbox"))
        self.assertIsNone(view.findChild(QWidget, "simulation.gpu_devices"))

        configuration = view.current_configuration()

        self.assertFalse(configuration.use_gpu)
        self.assertEqual(configuration.gpu_device_ids, [])


if __name__ == "__main__":
    unittest.main()
