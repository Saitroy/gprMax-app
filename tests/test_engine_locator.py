from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.infrastructure.runtime.bundled_runtime import (
    BundledRuntimeProvider,
)
from gprmax_workbench.infrastructure.runtime.engine_locator import EngineLocator
from gprmax_workbench.infrastructure.runtime.external_runtime import (
    ExternalRuntimeProvider,
)
from gprmax_workbench.infrastructure.runtime.path_manager import PathManager
from gprmax_workbench.infrastructure.settings import AppSettings, SettingsManager


class EngineLocatorTests(unittest.TestCase):
    def test_prefers_bundled_runtime_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as install_dir, tempfile.TemporaryDirectory() as settings_dir:
            install_root = Path(install_dir)
            bundled_python = install_root / "engine" / "python" / "python.exe"
            bundled_python.parent.mkdir(parents=True)
            bundled_python.write_text("", encoding="utf-8")

            settings_manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(settings_dir),
            )
            locator = EngineLocator(
                bundled_provider=BundledRuntimeProvider(
                    PathManager(
                        settings_manager=settings_manager,
                        installation_root=install_root,
                    )
                ),
                external_provider=ExternalRuntimeProvider(
                    development_python=install_root / "dev" / "python.exe"
                ),
            )

            resolution = locator.resolve(AppSettings())

            self.assertEqual(resolution.engine.mode.value, "bundled")
            self.assertEqual(resolution.engine.python_executable, bundled_python)

    def test_uses_configured_external_fallback_when_bundled_missing(self) -> None:
        with tempfile.TemporaryDirectory() as install_dir, tempfile.TemporaryDirectory() as settings_dir:
            install_root = Path(install_dir)
            external_python = install_root / "external" / "python.exe"
            external_python.parent.mkdir(parents=True)
            external_python.write_text("", encoding="utf-8")

            settings_manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(settings_dir),
            )
            locator = EngineLocator(
                bundled_provider=BundledRuntimeProvider(
                    PathManager(
                        settings_manager=settings_manager,
                        installation_root=install_root,
                    )
                ),
                external_provider=ExternalRuntimeProvider(
                    development_python=install_root / "dev" / "python.exe"
                ),
            )

            resolution = locator.resolve(
                AppSettings(
                    advanced_mode=True,
                    gprmax_python_executable=str(external_python),
                )
            )

            self.assertEqual(resolution.engine.mode.value, "external")
            self.assertEqual(resolution.engine.python_executable, external_python)
            self.assertIn("Bundled engine was not found", resolution.notes[0])


if __name__ == "__main__":
    unittest.main()

