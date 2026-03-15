from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ...domain.models import Project, ProjectMetadata
from ...infrastructure.project_store import JsonProjectStore
from .settings_service import SettingsService


class ProjectService:
    """Coordinates project lifecycle and persistence."""

    def __init__(
        self,
        project_store: JsonProjectStore,
        settings_service: SettingsService,
    ) -> None:
        self._project_store = project_store
        self._settings_service = settings_service

    def create_project(self, root: Path, name: str) -> Project:
        root = root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        for directory_name in ("generated", "runs", "results", "assets"):
            (root / directory_name).mkdir(exist_ok=True)

        project = Project(
            root=root,
            metadata=ProjectMetadata(
                name=name,
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            ),
        )
        self._project_store.save(project)
        self._settings_service.remember_project(root)
        return project

    def open_project(self, root: Path) -> Project:
        project = self._project_store.load(root)
        self._settings_service.remember_project(project.root)
        return project

    def project_file(self, root: Path) -> Path:
        return self._project_store.project_file(root)
