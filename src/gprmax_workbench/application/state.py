from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..domain.models import Project, SimulationRunRecord


@dataclass(slots=True)
class AppState:
    current_project: Project | None = None
    recent_projects: list[Path] = field(default_factory=list)
    active_run: SimulationRunRecord | None = None
    startup_project: Path | None = None
