from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.infrastructure.settings import AppSettings, SettingsManager


class SettingsManagerTests(unittest.TestCase):
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(temp_dir),
            )

            settings = AppSettings(
                recent_projects=[Path(temp_dir) / "project-a"],
                advanced_mode=True,
                gprmax_python_executable="python",
            )

            manager.save(settings)
            loaded = manager.load()

            self.assertEqual(loaded.recent_projects, settings.recent_projects)
            self.assertTrue(loaded.advanced_mode)
            self.assertEqual(loaded.gprmax_python_executable, "python")


if __name__ == "__main__":
    unittest.main()
