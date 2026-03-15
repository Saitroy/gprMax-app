from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .execution_status import SimulationMode
from .gprmax_config import SimulationRunConfig
from .model_entities import (
    EDITOR_GEOMETRY_KINDS,
    EDITOR_SOURCE_AXES,
    EDITOR_SOURCE_KINDS,
    EDITOR_WAVEFORM_KINDS,
)
from .models import BUILTIN_MATERIAL_IDENTIFIERS, Project, Vector3


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

    for index, material in enumerate(project.model.materials):
        if not material.identifier.strip():
            result.add_error(
                f"model.materials[{index}].identifier",
                "Material identifier must not be empty.",
            )
        _validate_positive_float(
            result,
            f"model.materials[{index}].relative_permittivity",
            material.relative_permittivity,
        )
        _validate_non_negative_float(
            result,
            f"model.materials[{index}].conductivity",
            material.conductivity,
        )
        _validate_positive_float(
            result,
            f"model.materials[{index}].relative_permeability",
            material.relative_permeability,
        )
        _validate_non_negative_float(
            result,
            f"model.materials[{index}].magnetic_loss",
            material.magnetic_loss,
        )

    for index, waveform in enumerate(project.model.waveforms):
        if not waveform.identifier.strip():
            result.add_error(
                f"model.waveforms[{index}].identifier",
                "Waveform identifier must not be empty.",
            )
        if not waveform.kind.strip():
            result.add_error(
                f"model.waveforms[{index}].kind",
                "Waveform kind must not be empty.",
            )
        elif waveform.kind not in EDITOR_WAVEFORM_KINDS:
            result.add_warning(
                f"model.waveforms[{index}].kind",
                f"Waveform kind '{waveform.kind}' is outside the current guided editor defaults.",
            )
        _validate_positive_float(
            result,
            f"model.waveforms[{index}].amplitude",
            waveform.amplitude,
        )
        _validate_positive_float(
            result,
            f"model.waveforms[{index}].center_frequency_hz",
            waveform.center_frequency_hz,
        )

    waveform_lookup = {item.identifier for item in project.model.waveforms}
    for index, source in enumerate(project.model.sources):
        if source.kind not in EDITOR_SOURCE_KINDS:
            result.add_error(
                f"model.sources[{index}].kind",
                f"Source kind '{source.kind}' is not supported by the current editor.",
            )
        if source.axis not in EDITOR_SOURCE_AXES:
            result.add_error(
                f"model.sources[{index}].axis",
                "Source axis must be one of x, y, or z.",
            )
        if source.identifier and not source.identifier.strip():
            result.add_error(
                f"model.sources[{index}].identifier",
                "Source identifier must not be blank when provided.",
            )
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
        if source.delay_s < 0:
            result.add_error(
                f"model.sources[{index}].delay_s",
                "Source delay must be zero or greater.",
            )
        if source.resistance_ohms is not None and source.resistance_ohms <= 0:
            result.add_error(
                f"model.sources[{index}].resistance_ohms",
                "Source resistance must be greater than zero when provided.",
            )
        _validate_position_within_domain(
            result,
            f"model.sources[{index}].position_m",
            source.position_m,
            project,
        )

    known_materials = set(material_ids) | BUILTIN_MATERIAL_IDENTIFIERS
    for index, primitive in enumerate(project.model.geometry):
        if primitive.kind not in EDITOR_GEOMETRY_KINDS:
            result.add_error(
                f"model.geometry[{index}].kind",
                f"Geometry kind '{primitive.kind}' is not supported by the current editor.",
            )
        _validate_geometry_primitive(result, project, index, primitive)
        for material_id in primitive.material_ids:
            if material_id not in known_materials:
                result.add_warning(
                    f"model.geometry[{index}].material_ids",
                    f"Geometry references unknown material '{material_id}'.",
                )
        if not primitive.material_ids:
            result.add_error(
                f"model.geometry[{index}].material_ids",
                "Geometry objects must reference at least one material.",
            )

    for index, receiver in enumerate(project.model.receivers):
        _validate_position_within_domain(
            result,
            f"model.receivers[{index}].position_m",
            receiver.position_m,
            project,
        )

    for index, geometry_view in enumerate(project.model.geometry_views):
        _validate_box_bounds(
            result,
            f"model.geometry_views[{index}]",
            _vector_to_dict(geometry_view.lower_left_m),
            _vector_to_dict(geometry_view.upper_right_m),
            project,
        )
        _validate_positive_float(
            result,
            f"model.geometry_views[{index}].resolution_m.x",
            geometry_view.resolution_m.x,
        )
        _validate_positive_float(
            result,
            f"model.geometry_views[{index}].resolution_m.y",
            geometry_view.resolution_m.y,
        )
        _validate_positive_float(
            result,
            f"model.geometry_views[{index}].resolution_m.z",
            geometry_view.resolution_m.z,
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


def validate_project_for_execution(
    project: Project,
    configuration: SimulationRunConfig,
) -> ValidationResult:
    result = validate_project(project)

    supported_source_kinds = {"hertzian_dipole", "magnetic_dipole", "voltage_source"}
    supported_geometry_kinds = {"box", "sphere", "cylinder"}

    for index, source in enumerate(project.model.sources):
        if source.kind not in supported_source_kinds:
            result.add_error(
                f"model.sources[{index}].kind",
                f"Source kind '{source.kind}' is not supported by the current input generator.",
            )

    for index, primitive in enumerate(project.model.geometry):
        if primitive.kind not in supported_geometry_kinds:
            result.add_error(
                f"model.geometry[{index}].kind",
                f"Geometry kind '{primitive.kind}' is not supported by the current input generator.",
            )

    if configuration.use_gpu and configuration.mpi_tasks:
        result.add_warning(
            "run_config",
            "GPU and MPI options are configured together. This is left as an advanced/future-ready path and may require environment-specific tuning.",
        )

    if configuration.mode == SimulationMode.GEOMETRY_ONLY and not project.model.geometry_views:
        result.add_warning(
            "model.geometry_views",
            "Geometry-only mode is enabled but no geometry views are configured.",
        )

    if configuration.num_model_runs < 1:
        result.add_error(
            "run_config.num_model_runs",
            "The number of model runs must be at least 1.",
        )

    if configuration.restart_from_model is not None and configuration.restart_from_model < 1:
        result.add_error(
            "run_config.restart_from_model",
            "Restart model index must be at least 1.",
        )

    if configuration.mpi_tasks is not None and configuration.mpi_tasks < 1:
        result.add_error(
            "run_config.mpi_tasks",
            "MPI tasks must be at least 1 when configured.",
        )

    return result


def _validate_positive_float(
    result: ValidationResult,
    path: str,
    value: float,
) -> None:
    if value <= 0:
        result.add_error(path, "Value must be greater than zero.")


def _validate_non_negative_float(
    result: ValidationResult,
    path: str,
    value: float,
) -> None:
    if value < 0:
        result.add_error(path, "Value must be zero or greater.")


def _validate_unique_identifiers(
    result: ValidationResult,
    path: str,
    identifiers: list[str],
    message: str,
) -> None:
    filtered = [identifier for identifier in identifiers if identifier.strip()]
    if len(filtered) != len(set(filtered)):
        result.add_error(path, message)


def _validate_position_within_domain(
    result: ValidationResult,
    path: str,
    value: Vector3,
    project: Project,
) -> None:
    for axis, coordinate, limit in (
        ("x", value.x, project.model.domain.size_m.x),
        ("y", value.y, project.model.domain.size_m.y),
        ("z", value.z, project.model.domain.size_m.z),
    ):
        if coordinate < 0 or coordinate > limit:
            result.add_error(
                f"{path}.{axis}",
                f"Coordinate must be within the domain range 0..{limit}.",
            )


def _validate_geometry_primitive(
    result: ValidationResult,
    project: Project,
    index: int,
    primitive,
) -> None:
    if primitive.kind == "box":
        _validate_box_bounds(
            result,
            f"model.geometry[{index}]",
            primitive.parameters.get("lower_left_m"),
            primitive.parameters.get("upper_right_m"),
            project,
        )
        return

    if primitive.kind == "sphere":
        center = primitive.parameters.get("center_m")
        radius = primitive.parameters.get("radius_m")
        if not isinstance(center, dict):
            result.add_error(
                f"model.geometry[{index}].parameters.center_m",
                "Sphere requires a center vector.",
            )
            return
        _validate_position_within_domain(
            result,
            f"model.geometry[{index}].parameters.center_m",
            Vector3(
                x=float(center.get("x", 0)),
                y=float(center.get("y", 0)),
                z=float(center.get("z", 0)),
            ),
            project,
        )
        if radius is None or float(radius) <= 0:
            result.add_error(
                f"model.geometry[{index}].parameters.radius_m",
                "Sphere radius must be greater than zero.",
            )
        return

    if primitive.kind == "cylinder":
        start = primitive.parameters.get("start_m")
        end = primitive.parameters.get("end_m")
        radius = primitive.parameters.get("radius_m")
        if not isinstance(start, dict) or not isinstance(end, dict):
            result.add_error(
                f"model.geometry[{index}].parameters",
                "Cylinder requires start and end vectors.",
            )
            return
        start_vector = Vector3(
            x=float(start.get("x", 0)),
            y=float(start.get("y", 0)),
            z=float(start.get("z", 0)),
        )
        end_vector = Vector3(
            x=float(end.get("x", 0)),
            y=float(end.get("y", 0)),
            z=float(end.get("z", 0)),
        )
        _validate_position_within_domain(
            result,
            f"model.geometry[{index}].parameters.start_m",
            start_vector,
            project,
        )
        _validate_position_within_domain(
            result,
            f"model.geometry[{index}].parameters.end_m",
            end_vector,
            project,
        )
        if start_vector == end_vector:
            result.add_error(
                f"model.geometry[{index}].parameters",
                "Cylinder start and end positions must differ.",
            )
        if radius is None or float(radius) <= 0:
            result.add_error(
                f"model.geometry[{index}].parameters.radius_m",
                "Cylinder radius must be greater than zero.",
            )


def _validate_box_bounds(
    result: ValidationResult,
    path: str,
    lower_left: object,
    upper_right: object,
    project: Project,
) -> None:
    if not isinstance(lower_left, dict) or not isinstance(upper_right, dict):
        result.add_error(path, "Object requires lower-left and upper-right vectors.")
        return

    for axis, domain_limit in (
        ("x", project.model.domain.size_m.x),
        ("y", project.model.domain.size_m.y),
        ("z", project.model.domain.size_m.z),
    ):
        minimum = float(lower_left.get(axis, 0))
        maximum = float(upper_right.get(axis, 0))
        if minimum < 0 or maximum < 0 or minimum > domain_limit or maximum > domain_limit:
            result.add_error(
                f"{path}.{axis}",
                f"Bounds must lie within the domain range 0..{domain_limit}.",
            )
        if minimum >= maximum:
            result.add_error(
                f"{path}.{axis}",
                "Lower bound must be smaller than upper bound.",
            )


def _vector_to_dict(vector: Vector3) -> dict[str, float]:
    return {"x": vector.x, "y": vector.y, "z": vector.z}
