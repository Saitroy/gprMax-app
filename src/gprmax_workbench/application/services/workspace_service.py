from __future__ import annotations

from pathlib import Path

from ...domain.models import Project
from ...domain.validation import ValidationResult, validate_project
from ..state import AppState
from .project_service import ProjectDraft, ProjectService
from .settings_service import SettingsService


class WorkspaceService:
    """Coordinates the current in-memory project and app session state."""

    def __init__(
        self,
        project_service: ProjectService,
        settings_service: SettingsService,
        state: AppState,
    ) -> None:
        self._project_service = project_service
        self._settings_service = settings_service
        self._state = state

    @property
    def state(self) -> AppState:
        return self._state

    def create_project(self, root: Path, name: str) -> Project:
        project = self._project_service.create_project(root=root, name=name)
        self._set_current_project(project, is_dirty=False)
        return project

    def open_project(self, target: Path) -> Project:
        project = self._project_service.open_project(target)
        self._set_current_project(project, is_dirty=False)
        return project

    def apply_draft(self, draft: ProjectDraft) -> ValidationResult:
        project = self.require_current_project()
        validation = self._project_service.apply_draft(project, draft)
        self._state.current_project_validation = validation
        self._state.current_project_dirty = True
        return validation

    def save_current_project(self) -> ValidationResult:
        project = self.require_current_project()
        validation = self._project_service.save_project(project)
        self._set_current_project(project, is_dirty=False)
        return validation

    def save_draft(self, draft: ProjectDraft) -> ValidationResult:
        validation = self.apply_draft(draft)
        if not validation.is_valid:
            return validation
        return self.save_current_project()

    def current_project_file(self) -> Path | None:
        project = self._state.current_project
        if project is None:
            return None
        return self._project_service.project_file(project.root)

    def require_current_project(self) -> Project:
        project = self._state.current_project
        if project is None:
            raise RuntimeError("No project is currently open.")
        return project

    def clear_current_project(self) -> None:
        self._state.current_project = None
        self._state.current_project_dirty = False
        self._state.current_project_validation = ValidationResult()

    def refresh_recent_projects(self) -> None:
        self._state.recent_projects = self._settings_service.recent_projects()

    def _set_current_project(self, project: Project, is_dirty: bool) -> None:
        self._state.current_project = project
        self._state.current_project_dirty = is_dirty
        self._state.current_project_validation = validate_project(project)
        self.refresh_recent_projects()
