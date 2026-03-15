from __future__ import annotations

import os
import sys
from pathlib import Path

from ..settings import SettingsManager


class PathManager:
    """Resolves installer-oriented application, engine, and user-data paths."""

    def __init__(
        self,
        *,
        settings_manager: SettingsManager,
        installation_root: Path | None = None,
    ) -> None:
        self._settings_manager = settings_manager
        self._installation_root = (
            installation_root or self._default_installation_root()
        ).resolve()

    @property
    def installation_root(self) -> Path:
        return self._installation_root

    @property
    def bundled_engine_root(self) -> Path:
        return self.installation_root / "engine"

    @property
    def bundled_manifest_path(self) -> Path:
        return self.bundled_engine_root / "manifest.json"

    @property
    def settings_directory(self) -> Path:
        return self._settings_manager.base_dir

    @property
    def logs_directory(self) -> Path:
        return self._settings_manager.logs_dir

    @property
    def cache_directory(self) -> Path:
        return self.settings_directory / "cache"

    @property
    def temp_directory(self) -> Path:
        return self.settings_directory / "temp"

    def bundled_python_executable(self) -> Path:
        for candidate in self.bundled_python_candidates():
            if candidate.exists():
                return candidate
        return self.bundled_python_candidates()[0]

    def bundled_python_candidates(self) -> list[Path]:
        engine_root = self.bundled_engine_root
        return [
            engine_root / "python" / "python.exe",
            engine_root / "python" / "python",
            engine_root / "python" / "bin" / "python",
            engine_root / "python" / "bin" / "python3",
        ]

    def ensure_user_runtime_directories(self) -> None:
        self.logs_directory.mkdir(parents=True, exist_ok=True)
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        self.temp_directory.mkdir(parents=True, exist_ok=True)

    def _default_installation_root(self) -> Path:
        override = os.getenv("GPRMAX_WORKBENCH_INSTALL_ROOT")
        if override:
            return Path(override).expanduser()
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[4]

