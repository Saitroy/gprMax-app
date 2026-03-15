from __future__ import annotations

from dataclasses import dataclass, field

from .models import Project


@dataclass(slots=True)
class ValidationResult:
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_project(project: Project) -> ValidationResult:
    result = ValidationResult()
    if not project.metadata.name.strip():
        result.errors.append("Project name must not be empty.")
    return result
