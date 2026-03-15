from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.models import RecentProject
from gprmax_workbench.infrastructure.settings import AppSettings, SettingsManager


class SettingsManagerTests(unittest.TestCase):
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(temp_dir),
            )

            settings = AppSettings(
                recent_projects=[
                    RecentProject(
                        path=Path(temp_dir) / "project-a",
                        name="Project A",
                        last_opened_at=datetime(2026, 3, 15, tzinfo=UTC),
                    )
                ],
                advanced_mode=True,
                gprmax_python_executable="python",
                language="en",
            )

            manager.save(settings)
            loaded = manager.load()

            self.assertEqual(len(loaded.recent_projects), 1)
            self.assertEqual(loaded.recent_projects[0].name, "Project A")
            self.assertTrue(loaded.advanced_mode)
            self.assertEqual(loaded.gprmax_python_executable, "python")
            self.assertEqual(loaded.language, "en")


if __name__ == "__main__":
    unittest.main()
