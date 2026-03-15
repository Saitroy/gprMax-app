from __future__ import annotations

from ...domain.models import Project
from ...domain.validation import ValidationIssue, ValidationResult, validate_project
from ..state import AppState


class ValidationService:
    """Provides validation queries tailored for the model editor UI."""

    def __init__(self, state: AppState) -> None:
        self._state = state

    def current_validation(self) -> ValidationResult:
        return self._state.current_project_validation

    def validate_model(self, project: Project) -> ValidationResult:
        validation = validate_project(project)
        self._state.current_project_validation = validation
        return validation

    def issues_for_prefixes(self, *prefixes: str) -> list[ValidationIssue]:
        issues = self.current_validation().issues
        if not prefixes:
            return issues
        return [
            issue
            for issue in issues
            if any(issue.path.startswith(prefix) for prefix in prefixes)
        ]

    def messages_for_prefixes(self, *prefixes: str) -> list[str]:
        return [
            f"{issue.severity.value}: {issue.message}"
            for issue in self.issues_for_prefixes(*prefixes)
        ]

    def summary_text(self, validation: ValidationResult | None = None) -> str:
        current = validation or self.current_validation()
        if not current.issues:
            return "Validation: no issues."
        return (
            f"Validation: {len(current.errors)} error(s), "
            f"{len(current.warnings)} warning(s)."
        )
