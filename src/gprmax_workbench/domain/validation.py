from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .models import BUILTIN_MATERIAL_IDENTIFIERS, Project


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(slots=True)
class ValidationIssue:
    path: str
    message: str
    severity: ValidationSeverity


@dataclass(slots=True)
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def errors(self) -> list[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == ValidationSeverity.ERROR
        ]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == ValidationSeverity.WARNING
        ]

    def add_error(self, path: str, message: str) -> None:
        self.issues.append(
            ValidationIssue(
                path=path,
                message=message,
                severity=ValidationSeverity.ERROR,
            )
        )

    def add_warning(self, path: str, message: str) -> None:
        self.issues.append(
            ValidationIssue(
                path=path,
                message=message,
                severity=ValidationSeverity.WARNING,
            )
        )


def validate_project(project: Project) -> ValidationResult:
    result = ValidationResult()

    if not project.metadata.name.strip():
        result.add_error("metadata.name", "Project name must not be empty.")

    if not project.model.title.strip():
        result.add_warning(
            "model.title",
            "Model title is empty. The generated input should usually include a title.",
        )

    _validate_positive_float(
        result,
        "model.domain.size_m.x",
        project.model.domain.size_m.x,
    )
    _validate_positive_float(
        result,
        "model.domain.size_m.y",
        project.model.domain.size_m.y,
    )
    _validate_positive_float(
        result,
        "model.domain.size_m.z",
        project.model.domain.size_m.z,
    )
    _validate_positive_float(
        result,
        "model.domain.resolution_m.x",
        project.model.domain.resolution_m.x,
    )
    _validate_positive_float(
        result,
        "model.domain.resolution_m.y",
        project.model.domain.resolution_m.y,
    )
    _validate_positive_float(
        result,
        "model.domain.resolution_m.z",
        project.model.domain.resolution_m.z,
    )
    _validate_positive_float(
        result,
        "model.domain.time_window_s",
        project.model.domain.time_window_s,
    )

    for name, value in {
        "x_min": project.model.domain.pml_cells.x_min,
        "y_min": project.model.domain.pml_cells.y_min,
        "z_min": project.model.domain.pml_cells.z_min,
        "x_max": project.model.domain.pml_cells.x_max,
        "y_max": project.model.domain.pml_cells.y_max,
        "z_max": project.model.domain.pml_cells.z_max,
    }.items():
        if value < 0:
            result.add_error(
                f"model.domain.pml_cells.{name}",
                "PML cell counts must be zero or positive integers.",
            )

    material_ids = [item.identifier for item in project.model.materials]
    waveform_ids = [item.identifier for item in project.model.waveforms]
    receiver_ids = [
        item.identifier for item in project.model.receivers if item.identifier
    ]
    source_ids = [item.identifier for item in project.model.sources if item.identifier]

    _validate_unique_identifiers(
        result,
        "model.materials",
        material_ids,
        "Material identifiers must be unique.",
    )
    _validate_unique_identifiers(
        result,
        "model.waveforms",
        waveform_ids,
        "Waveform identifiers must be unique.",
    )
    _validate_unique_identifiers(
        result,
        "model.receivers",
        receiver_ids,
        "Receiver identifiers must be unique when provided.",
    )
    _validate_unique_identifiers(
        result,
        "model.sources",
        source_ids,
        "Source identifiers must be unique when provided.",
    )

    waveform_lookup = {item.identifier for item in project.model.waveforms}
    for index, source in enumerate(project.model.sources):
        if not source.waveform_id.strip():
            result.add_warning(
                f"model.sources[{index}].waveform_id",
                "Source has no waveform reference yet.",
            )
        elif source.waveform_id not in waveform_lookup:
            result.add_warning(
                f"model.sources[{index}].waveform_id",
                f"Waveform '{source.waveform_id}' is not defined in this project.",
            )

    known_materials = set(material_ids) | BUILTIN_MATERIAL_IDENTIFIERS
    for index, primitive in enumerate(project.model.geometry):
        for material_id in primitive.material_ids:
            if material_id not in known_materials:
                result.add_warning(
                    f"model.geometry[{index}].material_ids",
                    f"Geometry references unknown material '{material_id}'.",
                )

    if not project.model.sources:
        result.add_warning(
            "model.sources",
            "No sources are defined yet. The project can be saved but cannot run a full simulation.",
        )

    if not project.model.receivers:
        result.add_warning(
            "model.receivers",
            "No receivers are defined yet. Results collection is not configured.",
        )

    return result


def _validate_positive_float(
    result: ValidationResult,
    path: str,
    value: float,
) -> None:
    if value <= 0:
        result.add_error(path, "Value must be greater than zero.")


def _validate_unique_identifiers(
    result: ValidationResult,
    path: str,
    identifiers: list[str],
    message: str,
) -> None:
    filtered = [identifier for identifier in identifiers if identifier.strip()]
    if len(filtered) != len(set(filtered)):
        result.add_error(path, message)
