from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ...domain.models import Project, Vector3, default_project
from ...domain.validation import ValidationResult, validate_project
from ...infrastructure.project_store import JsonProjectStore
from .settings_service import SettingsService


@dataclass(slots=True)
class ProjectDraft:
    project_name: str
    description: str
    model_title: str
    domain_size_m: Vector3
    resolution_m: Vector3
    time_window_s: float


class ProjectValidationError(ValueError):
    def __init__(self, validation: ValidationResult) -> None:
        self.validation = validation
        message = "; ".join(
            f"{issue.path}: {issue.message}" for issue in validation.errors
        )
        super().__init__(message or "Project validation failed.")


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
        project_root = self._resolve_project_root(root)
        project_root.mkdir(parents=True, exist_ok=True)

        for directory_name in ("generated", "runs", "results", "assets"):
            (project_root / directory_name).mkdir(exist_ok=True)

        project = default_project(name=name, root=project_root)
        self._project_store.save(project)
        self._settings_service.remember_project(project)
        return project

    def open_project(self, target: Path) -> Project:
        project = self._project_store.load(target)
        self._settings_service.remember_project(project)
        return project

    def save_project(self, project: Project) -> ValidationResult:
        validation = validate_project(project)
        if not validation.is_valid:
            raise ProjectValidationError(validation)

        project.metadata.updated_at = datetime.now(tz=UTC)
        self._project_store.save(project)
        self._settings_service.remember_project(project)
        return validation

    def apply_draft(self, project: Project, draft: ProjectDraft) -> ValidationResult:
        project.metadata.name = draft.project_name.strip()
        project.metadata.description = draft.description.strip()
        project.model.title = draft.model_title.strip()
        project.model.domain.size_m = draft.domain_size_m
        project.model.domain.resolution_m = draft.resolution_m
        project.model.domain.time_window_s = draft.time_window_s
        return validate_project(project)

    def project_file(self, root: Path) -> Path:
        return self._project_store.project_file(root)

    def _resolve_project_root(self, target: Path) -> Path:
        normalized = target.expanduser().resolve()
        if normalized.suffix == ".json":
            return normalized.parent
        return normalized
