from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..domain.models import Project, RecentProject, SimulationRunRecord
from ..domain.validation import ValidationResult


@dataclass(slots=True)
class AppState:
    current_project: Project | None = None
    recent_projects: list[RecentProject] = field(default_factory=list)
    current_project_validation: ValidationResult = field(default_factory=ValidationResult)
    current_project_dirty: bool = False
    active_run: SimulationRunRecord | None = None
    startup_project: Path | None = None
