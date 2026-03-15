from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.engine_config import EngineConfig, EngineMode, EngineResolution
from gprmax_workbench.infrastructure.runtime.diagnostics import (
    ProbeResult,
    RuntimeDiagnostics,
)
from gprmax_workbench.infrastructure.runtime.path_manager import PathManager
from gprmax_workbench.infrastructure.runtime.versioning import VersioningService
from gprmax_workbench.infrastructure.settings import SettingsManager


class _FakeProbe:
    def __init__(self, result: ProbeResult) -> None:
        self._result = result

    def probe(self, python_executable: Path, module_name: str) -> ProbeResult:
        return self._result


class RuntimeDiagnosticsTests(unittest.TestCase):
    def test_marks_cpu_ready_and_gpu_mpi_optional(self) -> None:
        with tempfile.TemporaryDirectory() as install_dir, tempfile.TemporaryDirectory() as settings_dir:
            install_root = Path(install_dir)
            bundled_python = install_root / "engine" / "python" / "python.exe"
            bundled_python.parent.mkdir(parents=True)
            bundled_python.write_text("", encoding="utf-8")

            settings_manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(settings_dir),
            )
            diagnostics = RuntimeDiagnostics(
                path_manager=PathManager(
                    settings_manager=settings_manager,
                    installation_root=install_root,
                ),
                versioning=VersioningService(),
                probe=_FakeProbe(
                    ProbeResult(
                        python_exists=True,
                        module_available=True,
                        gprmax_version="4.0.0",
                        gpu_available=False,
                        mpi_available=False,
                    )
                ),
            )

            info = diagnostics.inspect(
                EngineResolution(
                    engine=EngineConfig(
                        mode=EngineMode.BUNDLED,
                        python_executable=bundled_python,
                        engine_root=install_root / "engine",
                        installation_root=install_root,
                        source_label="Bundled engine",
                    ),
                    notes=["Using bundled engine from the installation directory."],
                )
            )

            self.assertTrue(info.is_healthy)
            self.assertEqual(info.gprmax_version, "4.0.0")
            self.assertEqual(info.capabilities[0].code, "cpu")
            self.assertEqual(info.capabilities[0].level.value, "ready")
            self.assertEqual(info.capabilities[1].level.value, "optional")
            self.assertEqual(info.capabilities[2].level.value, "optional")

    def test_reports_missing_bundled_engine_and_unhealthy_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as install_dir, tempfile.TemporaryDirectory() as settings_dir:
            install_root = Path(install_dir)
            missing_python = install_root / "engine" / "python" / "python.exe"
            settings_manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(settings_dir),
            )
            diagnostics = RuntimeDiagnostics(
                path_manager=PathManager(
                    settings_manager=settings_manager,
                    installation_root=install_root,
                ),
                versioning=VersioningService(),
                probe=_FakeProbe(
                    ProbeResult(
                        python_exists=False,
                        module_available=False,
                        gprmax_version=None,
                        gpu_available=False,
                        mpi_available=False,
                        error=f"Python executable not found: {missing_python}",
                    )
                ),
            )

            info = diagnostics.inspect(
                EngineResolution(
                    engine=EngineConfig(
                        mode=EngineMode.BUNDLED,
                        python_executable=missing_python,
                        engine_root=install_root / "engine",
                        installation_root=install_root,
                        source_label="Bundled engine",
                    ),
                    notes=["Bundled engine was not found at expected path: missing"],
                )
            )

            self.assertFalse(info.is_healthy)
            self.assertTrue(any("Bundled engine directory is missing" in item for item in info.diagnostics))
            self.assertTrue(any("Python executable not found" in item for item in info.diagnostics))


if __name__ == "__main__":
    unittest.main()
