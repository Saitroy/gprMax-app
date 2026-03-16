from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.infrastructure.runtime.path_manager import PathManager
from gprmax_workbench.infrastructure.settings import SettingsManager


class PathManagerTests(unittest.TestCase):
    def test_resolves_installer_oriented_paths(self) -> None:
        with tempfile.TemporaryDirectory() as install_dir, tempfile.TemporaryDirectory() as settings_dir:
            manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(settings_dir),
            )
            path_manager = PathManager(
                settings_manager=manager,
                installation_root=Path(install_dir),
            )

            self.assertEqual(path_manager.installation_root, Path(install_dir))
            self.assertEqual(path_manager.bundled_engine_root, Path(install_dir) / "engine")
            self.assertEqual(path_manager.bundled_manifest_path, Path(install_dir) / "engine" / "manifest.json")
            self.assertEqual(path_manager.settings_directory, Path(settings_dir))
            self.assertEqual(path_manager.logs_directory, Path(settings_dir) / "logs")
            self.assertEqual(path_manager.cache_directory, Path(settings_dir) / "cache")
            self.assertEqual(path_manager.temp_directory, Path(settings_dir) / "temp")

    def test_prefers_existing_bundled_python_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as install_dir, tempfile.TemporaryDirectory() as settings_dir:
            install_root = Path(install_dir)
            python_dir = install_root / "engine" / "python" / "Scripts"
            python_dir.mkdir(parents=True)
            expected = python_dir / "python.exe"
            expected.write_text("", encoding="utf-8")

            manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(settings_dir),
            )
            path_manager = PathManager(
                settings_manager=manager,
                installation_root=install_root,
            )

            self.assertEqual(path_manager.bundled_python_executable(), expected)


if __name__ == "__main__":
    unittest.main()
