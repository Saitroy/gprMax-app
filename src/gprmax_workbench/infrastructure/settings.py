from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..domain.models import RecentProject

SETTINGS_SCHEMA_NAME = "gprmax-workbench-settings"
SETTINGS_SCHEMA_VERSION = 4
DEFAULT_INTERFACE_LANGUAGE = "ru"


@dataclass(slots=True)
class AppSettings:
    recent_projects: list[RecentProject] = field(default_factory=list)
    advanced_mode: bool = False
    gprmax_python_executable: str | None = None
    language: str = DEFAULT_INTERFACE_LANGUAGE
    ui_state: dict[str, object] = field(default_factory=dict)


class SettingsManager:
    """Persists application settings outside the project workspace."""

    def __init__(self, app_name: str, base_dir: Path | None = None) -> None:
        self._app_name = app_name
        self._base_dir = base_dir or default_settings_dir(app_name)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    @property
    def settings_path(self) -> Path:
        return self._base_dir / "settings.json"

    @property
    def logs_dir(self) -> Path:
        return self._base_dir / "logs"

    def load(self) -> AppSettings:
        if not self.settings_path.exists():
            return AppSettings()

        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        recent_projects = [
            _recent_project_from_payload(item)
            for item in payload.get("recent_projects", [])
            if isinstance(item, dict)
        ]
        return AppSettings(
            recent_projects=recent_projects,
            advanced_mode=bool(payload.get("advanced_mode", False)),
            gprmax_python_executable=payload.get("gprmax_python_executable"),
            language=str(payload.get("language", DEFAULT_INTERFACE_LANGUAGE)),
            ui_state=_ui_state_from_payload(payload.get("ui_state")),
        )

    def save(self, settings: AppSettings) -> None:
        payload = {
            "schema": {
                "name": SETTINGS_SCHEMA_NAME,
                "version": SETTINGS_SCHEMA_VERSION,
            },
            "recent_projects": [
                _recent_project_to_payload(item) for item in settings.recent_projects
            ],
            "advanced_mode": settings.advanced_mode,
            "gprmax_python_executable": settings.gprmax_python_executable,
            "language": settings.language,
            "ui_state": settings.ui_state,
        }
        self.settings_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def default_settings_dir(app_name: str) -> Path:
    system = platform.system()
    if system == "Windows":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / app_name
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / app_name


def _recent_project_to_payload(project: RecentProject) -> dict[str, str]:
    return {
        "path": str(project.path),
        "name": project.name,
        "last_opened_at": project.last_opened_at.isoformat(),
    }


def _recent_project_from_payload(payload: dict[str, str]) -> RecentProject:
    return RecentProject(
        path=Path(payload["path"]).expanduser(),
        name=payload.get("name", ""),
        last_opened_at=datetime.fromisoformat(payload["last_opened_at"]),
    )


def _ui_state_from_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items()}
