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
from gprmax_workbench.domain.engine_config import EngineConfig, EngineMode
from gprmax_workbench.domain.runtime_info import RuntimeInfo
from gprmax_workbench.infrastructure.settings import AppSettings
from gprmax_workbench.ui.views.settings_view import SettingsView


class SettingsViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_hides_gpu_capability_from_user_facing_summary(self) -> None:
        view = SettingsView(LocalizationService("en"))
        runtime_info = RuntimeInfo(
            engine=EngineConfig(
                mode=EngineMode.BUNDLED,
                python_executable=Path("python"),
            ),
            app_version="test",
            bundled_engine_version="test",
            gprmax_version="test",
            settings_path=Path("settings.json"),
            logs_directory=Path("logs"),
            cache_directory=Path("cache"),
            temp_directory=Path("temp"),
            capabilities=[
                CapabilityStatus(code="cpu", level=CapabilityLevel.READY),
                CapabilityStatus(code="gpu", level=CapabilityLevel.OPTIONAL),
                CapabilityStatus(code="mpi", level=CapabilityLevel.OPTIONAL),
            ],
            is_healthy=True,
        )

        view.set_settings(AppSettings(), runtime_info)

        capability_text = view._capabilities_label.text()
        self.assertIn("CPU", capability_text)
        self.assertIn("MPI", capability_text)
        self.assertNotIn("GPU", capability_text)


if __name__ == "__main__":
    unittest.main()
