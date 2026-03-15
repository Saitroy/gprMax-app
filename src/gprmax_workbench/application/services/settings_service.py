from __future__ import annotations

from datetime import UTC, datetime

from ...domain.models import Project, RecentProject
from ...infrastructure.settings import AppSettings, SettingsManager


class SettingsService:
    """Wraps persisted application settings with product-level operations."""

    def __init__(self, settings_manager: SettingsManager) -> None:
        self._settings_manager = settings_manager
        self._settings = settings_manager.load()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def recent_projects(self) -> list[RecentProject]:
        return list(self._settings.recent_projects)

    def remember_project(self, project: Project) -> None:
        normalized = project.root.expanduser().resolve()
        entry = RecentProject(
            path=normalized,
            name=project.metadata.name,
            last_opened_at=datetime.now(tz=UTC),
        )
        recent_projects = [entry]
        recent_projects.extend(
            item for item in self._settings.recent_projects if item.path != normalized
        )
        self._settings.recent_projects = recent_projects[:10]
        self._settings_manager.save(self._settings)

    def update_preferences(
        self,
        *,
        advanced_mode: bool,
        gprmax_python_executable: str | None,
        language: str,
    ) -> AppSettings:
        runtime = (gprmax_python_executable or "").strip() or None
        self._settings.advanced_mode = advanced_mode
        self._settings.gprmax_python_executable = runtime
        self._settings.language = language
        self._settings_manager.save(self._settings)
        return self._settings

    def runtime_summary(self) -> dict[str, str]:
        return {
            "settings_file": str(self._settings_manager.settings_path),
            "logs_directory": str(self._settings_manager.logs_dir),
            "gprmax_runtime": self._settings.gprmax_python_executable or "",
            "advanced_mode": "true" if self._settings.advanced_mode else "false",
            "recent_projects": str(len(self._settings.recent_projects)),
            "interface_language": self._settings.language,
        }
