from __future__ import annotations

from pathlib import Path

from ...infrastructure.settings import AppSettings, SettingsManager


class SettingsService:
    """Wraps persisted application settings with product-level operations."""

    def __init__(self, settings_manager: SettingsManager) -> None:
        self._settings_manager = settings_manager
        self._settings = settings_manager.load()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def recent_projects(self) -> list[Path]:
        return list(self._settings.recent_projects)

    def remember_project(self, project_root: Path) -> None:
        normalized = project_root.expanduser().resolve()
        recent_projects = [normalized]
        recent_projects.extend(
            path for path in self._settings.recent_projects if path != normalized
        )
        self._settings.recent_projects = recent_projects[:10]
        self._settings_manager.save(self._settings)

    def runtime_summary(self) -> dict[str, str]:
        return {
            "Settings file": str(self._settings_manager.settings_path),
            "Logs directory": str(self._settings_manager.logs_dir),
            "gprMax runtime": self._settings.gprmax_python_executable or "python",
            "Advanced mode": "Enabled" if self._settings.advanced_mode else "Disabled",
        }
