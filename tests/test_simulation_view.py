from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.domain.capability_status import CapabilityLevel, CapabilityStatus
from gprmax_workbench.ui.views.simulation_view import SimulationView


class SimulationViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_disables_gpu_controls_when_capability_is_not_ready(self) -> None:
        view = SimulationView(
            localization=LocalizationService("en"),
            runtime_label="Bundled runtime",
        )

        view.set_gpu_capability(
            CapabilityStatus(
                code="gpu",
                level=CapabilityLevel.OPTIONAL,
                detail="pycuda is not available in the current runtime.",
            )
        )

        gpu_checkbox = view.findChild(type(view._gpu_checkbox), "simulation.gpu_checkbox")
        gpu_devices = view.findChild(type(view._gpu_devices_edit), "simulation.gpu_devices")
        gpu_status = view.findChild(type(view._gpu_status_label), "simulation.gpu_status")

        assert gpu_checkbox is not None
        assert gpu_devices is not None
        assert gpu_status is not None

        self.assertFalse(gpu_checkbox.isEnabled())
        self.assertFalse(gpu_checkbox.isChecked())
        self.assertFalse(gpu_devices.isEnabled())
        self.assertIn("pycuda", gpu_status.text())


if __name__ == "__main__":
    unittest.main()
