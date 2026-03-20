from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..domain.models import (
    AntennaModelDefinition,
    GeometryImportDefinition,
    PROJECT_SCHEMA_NAME,
    PROJECT_SCHEMA_VERSION,
    GeometryPrimitive,
    GeometryView,
    MaterialDefinition,
    ModelDomain,
    PmlCells,
    Project,
    ProjectMetadata,
    ProjectModel,
    ReceiverDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
)

PROJECT_FILENAME = "project.gprwb.json"


class JsonProjectStore:
    """Stores project metadata and editor state in a JSON manifest."""

    def project_file(self, root: Path) -> Path:
        normalized_root = self._resolve_project_root(root)
        return normalized_root / PROJECT_FILENAME

    def save(self, project: Project) -> Path:
        project.root.mkdir(parents=True, exist_ok=True)
        project_file = self.project_file(project.root)
        payload = {
            "schema": {
                "name": PROJECT_SCHEMA_NAME,
                "version": PROJECT_SCHEMA_VERSION,
            },
            "metadata": {
                "name": project.metadata.name,
                "description": project.metadata.description,
                "created_at": project.metadata.created_at.isoformat(),
                "updated_at": project.metadata.updated_at.isoformat(),
            },
            "model": {
                "title": project.model.title,
                "scan_trace_count": project.model.scan_trace_count,
                "notes": project.model.notes,
                "tags": list(project.model.tags),
                "domain": {
                    "size_m": _vector_to_payload(project.model.domain.size_m),
                    "resolution_m": _vector_to_payload(
                        project.model.domain.resolution_m
                    ),
                    "time_window_s": project.model.domain.time_window_s,
                    "pml_cells": _pml_to_payload(project.model.domain.pml_cells),
                },
                "materials": [
                    _material_to_payload(item) for item in project.model.materials
                ],
                "waveforms": [
                    _waveform_to_payload(item) for item in project.model.waveforms
                ],
                "sources": [_source_to_payload(item) for item in project.model.sources],
                "receivers": [
                    _receiver_to_payload(item) for item in project.model.receivers
                ],
                "geometry": [
                    _geometry_to_payload(item) for item in project.model.geometry
                ],
                "geometry_imports": [
                    _geometry_import_to_payload(item)
                    for item in project.model.geometry_imports
                ],
                "antenna_models": [
                    _antenna_model_to_payload(item)
                    for item in project.model.antenna_models
                ],
                "geometry_views": [
                    _geometry_view_to_payload(item)
                    for item in project.model.geometry_views
                ],
                "python_blocks": list(project.model.python_blocks),
            },
            "advanced": {
                "raw_input_overrides": list(project.advanced_input_overrides),
            },
        }
        project_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return project_file

    def load(self, target: Path) -> Project:
        project_root = self._resolve_project_root(target)
        project_file = self.project_file(project_root)
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        metadata = payload["metadata"]
        model_payload = payload.get("model", {})
        domain_payload = model_payload.get("domain", {})
        advanced_payload = payload.get("advanced", {})

        return Project(
            root=project_root,
            metadata=ProjectMetadata(
                name=metadata["name"],
                description=metadata.get("description", ""),
                created_at=_parse_datetime(metadata["created_at"]),
                updated_at=_parse_datetime(metadata["updated_at"]),
            ),
            model=ProjectModel(
                title=model_payload.get("title", ""),
                scan_trace_count=(
                    int(model_payload["scan_trace_count"])
                    if model_payload.get("scan_trace_count") is not None
                    else None
                ),
                notes=str(model_payload.get("notes", "")),
                tags=[str(item) for item in model_payload.get("tags", [])],
                domain=ModelDomain(
                    size_m=_vector_from_payload(
                        domain_payload.get("size_m"),
                        default=Vector3(x=1.0, y=1.0, z=0.1),
                    ),
                    resolution_m=_vector_from_payload(
                        domain_payload.get("resolution_m"),
                        default=Vector3(x=0.01, y=0.01, z=0.01),
                    ),
                    time_window_s=float(domain_payload.get("time_window_s", 3e-9)),
                    pml_cells=_pml_from_payload(domain_payload.get("pml_cells")),
                ),
                materials=[
                    _material_from_payload(item)
                    for item in model_payload.get("materials", [])
                    if isinstance(item, dict)
                ],
                waveforms=[
                    _waveform_from_payload(item)
                    for item in model_payload.get("waveforms", [])
                    if isinstance(item, dict)
                ],
                sources=[
                    _source_from_payload(item)
                    for item in model_payload.get("sources", [])
                    if isinstance(item, dict)
                ],
                receivers=[
                    _receiver_from_payload(item)
                    for item in model_payload.get("receivers", [])
                    if isinstance(item, dict)
                ],
                geometry=[
                    _geometry_from_payload(item)
                    for item in model_payload.get("geometry", [])
                    if isinstance(item, dict)
                ],
                geometry_imports=[
                    _geometry_import_from_payload(item)
                    for item in model_payload.get("geometry_imports", [])
                    if isinstance(item, dict)
                ],
                antenna_models=[
                    _antenna_model_from_payload(item)
                    for item in model_payload.get("antenna_models", [])
                    if isinstance(item, dict)
                ],
                geometry_views=[
                    _geometry_view_from_payload(item)
                    for item in model_payload.get("geometry_views", [])
                    if isinstance(item, dict)
                ],
                python_blocks=[
                    str(item) for item in model_payload.get("python_blocks", [])
                ],
            ),
            advanced_input_overrides=[
                str(item) for item in advanced_payload.get("raw_input_overrides", [])
            ],
        )

    def _resolve_project_root(self, target: Path) -> Path:
        normalized = target.expanduser().resolve()
        if normalized.is_file():
            return normalized.parent
        if normalized.name == PROJECT_FILENAME:
            return normalized.parent
        return normalized


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _vector_to_payload(vector: Vector3) -> dict[str, float]:
    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_payload(value: Any, default: Vector3) -> Vector3:
    if not isinstance(value, dict):
        return default
    return Vector3(
        x=float(value.get("x", default.x)),
        y=float(value.get("y", default.y)),
        z=float(value.get("z", default.z)),
    )


def _pml_to_payload(pml: PmlCells) -> dict[str, int]:
    return {
        "x_min": pml.x_min,
        "y_min": pml.y_min,
        "z_min": pml.z_min,
        "x_max": pml.x_max,
        "y_max": pml.y_max,
        "z_max": pml.z_max,
    }


def _pml_from_payload(value: Any) -> PmlCells:
    if not isinstance(value, dict):
        return PmlCells()
    return PmlCells(
        x_min=int(value.get("x_min", 10)),
        y_min=int(value.get("y_min", 10)),
        z_min=int(value.get("z_min", 10)),
        x_max=int(value.get("x_max", 10)),
        y_max=int(value.get("y_max", 10)),
        z_max=int(value.get("z_max", 10)),
    )


def _material_to_payload(material: MaterialDefinition) -> dict[str, float | str]:
    return {
        "identifier": material.identifier,
        "relative_permittivity": material.relative_permittivity,
        "conductivity": material.conductivity,
        "relative_permeability": material.relative_permeability,
        "magnetic_loss": material.magnetic_loss,
        "notes": material.notes,
        "tags": list(material.tags),
    }


def _material_from_payload(value: dict[str, Any]) -> MaterialDefinition:
    return MaterialDefinition(
        identifier=str(value.get("identifier", "")),
        relative_permittivity=float(value.get("relative_permittivity", 1.0)),
        conductivity=float(value.get("conductivity", 0.0)),
        relative_permeability=float(value.get("relative_permeability", 1.0)),
        magnetic_loss=float(value.get("magnetic_loss", 0.0)),
        notes=str(value.get("notes", "")),
        tags=[str(item) for item in value.get("tags", [])],
    )


def _waveform_to_payload(waveform: WaveformDefinition) -> dict[str, float | str]:
    return {
        "identifier": waveform.identifier,
        "kind": waveform.kind,
        "amplitude": waveform.amplitude,
        "center_frequency_hz": waveform.center_frequency_hz,
        "notes": waveform.notes,
        "tags": list(waveform.tags),
    }


def _waveform_from_payload(value: dict[str, Any]) -> WaveformDefinition:
    return WaveformDefinition(
        identifier=str(value.get("identifier", "")),
        kind=str(value.get("kind", "")),
        amplitude=float(value.get("amplitude", 1.0)),
        center_frequency_hz=float(value.get("center_frequency_hz", 0.0)),
        notes=str(value.get("notes", "")),
        tags=[str(item) for item in value.get("tags", [])],
    )


def _source_to_payload(source: SourceDefinition) -> dict[str, Any]:
    return {
        "identifier": source.identifier,
        "kind": source.kind,
        "axis": source.axis,
        "position_m": _vector_to_payload(source.position_m),
        "waveform_id": source.waveform_id,
        "delay_s": source.delay_s,
        "resistance_ohms": source.resistance_ohms,
        "notes": source.notes,
        "tags": list(source.tags),
        "parameters": dict(source.parameters),
    }


def _source_from_payload(value: dict[str, Any]) -> SourceDefinition:
    return SourceDefinition(
        identifier=str(value.get("identifier", "")),
        kind=str(value.get("kind", "")),
        axis=str(value.get("axis", "z")),
        position_m=_vector_from_payload(
            value.get("position_m"),
            default=Vector3(x=0.0, y=0.0, z=0.0),
        ),
        waveform_id=str(value.get("waveform_id", "")),
        delay_s=float(value.get("delay_s", 0.0)),
        resistance_ohms=(
            float(value["resistance_ohms"])
            if value.get("resistance_ohms") is not None
            else None
        ),
        notes=str(value.get("notes", "")),
        tags=[str(item) for item in value.get("tags", [])],
        parameters=dict(value.get("parameters", {}))
        if isinstance(value.get("parameters"), dict)
        else {},
    )


def _receiver_to_payload(receiver: ReceiverDefinition) -> dict[str, Any]:
    return {
        "identifier": receiver.identifier,
        "position_m": _vector_to_payload(receiver.position_m),
        "outputs": list(receiver.outputs),
        "notes": receiver.notes,
        "tags": list(receiver.tags),
    }


def _receiver_from_payload(value: dict[str, Any]) -> ReceiverDefinition:
    return ReceiverDefinition(
        identifier=str(value.get("identifier", "")),
        position_m=_vector_from_payload(
            value.get("position_m"),
            default=Vector3(x=0.0, y=0.0, z=0.0),
        ),
        outputs=[str(item) for item in value.get("outputs", [])],
        notes=str(value.get("notes", "")),
        tags=[str(item) for item in value.get("tags", [])],
    )


def _geometry_to_payload(geometry: GeometryPrimitive) -> dict[str, Any]:
    return {
        "kind": geometry.kind,
        "label": geometry.label,
        "material_ids": list(geometry.material_ids),
        "dielectric_smoothing": geometry.dielectric_smoothing,
        "notes": geometry.notes,
        "tags": list(geometry.tags),
        "parameters": dict(geometry.parameters),
    }


def _geometry_from_payload(value: dict[str, Any]) -> GeometryPrimitive:
    return GeometryPrimitive(
        kind=str(value.get("kind", "")),
        label=str(value.get("label", "")),
        material_ids=[str(item) for item in value.get("material_ids", [])],
        dielectric_smoothing=bool(value.get("dielectric_smoothing", True)),
        notes=str(value.get("notes", "")),
        tags=[str(item) for item in value.get("tags", [])],
        parameters=dict(value.get("parameters", {}))
        if isinstance(value.get("parameters"), dict)
        else {},
    )


def _geometry_view_to_payload(view: GeometryView) -> dict[str, Any]:
    return {
        "lower_left_m": _vector_to_payload(view.lower_left_m),
        "upper_right_m": _vector_to_payload(view.upper_right_m),
        "resolution_m": _vector_to_payload(view.resolution_m),
        "filename": view.filename,
        "mode": view.mode,
    }


def _geometry_view_from_payload(value: dict[str, Any]) -> GeometryView:
    return GeometryView(
        lower_left_m=_vector_from_payload(
            value.get("lower_left_m"),
            default=Vector3(x=0.0, y=0.0, z=0.0),
        ),
        upper_right_m=_vector_from_payload(
            value.get("upper_right_m"),
            default=Vector3(x=1.0, y=1.0, z=0.1),
        ),
        resolution_m=_vector_from_payload(
            value.get("resolution_m"),
            default=Vector3(x=0.01, y=0.01, z=0.01),
        ),
        filename=str(value.get("filename", "geometry")),
        mode=str(value.get("mode", "n")),
    )


def _geometry_import_to_payload(geometry_import: GeometryImportDefinition) -> dict[str, Any]:
    return {
        "identifier": geometry_import.identifier,
        "position_m": _vector_to_payload(geometry_import.position_m),
        "geometry_hdf5": geometry_import.geometry_hdf5,
        "materials_file": geometry_import.materials_file,
        "dielectric_smoothing": geometry_import.dielectric_smoothing,
        "notes": geometry_import.notes,
        "tags": list(geometry_import.tags),
    }


def _geometry_import_from_payload(value: dict[str, Any]) -> GeometryImportDefinition:
    return GeometryImportDefinition(
        identifier=str(value.get("identifier", "")),
        position_m=_vector_from_payload(
            value.get("position_m"),
            default=Vector3(x=0.0, y=0.0, z=0.0),
        ),
        geometry_hdf5=str(value.get("geometry_hdf5", "")),
        materials_file=str(value.get("materials_file", "")),
        dielectric_smoothing=bool(value.get("dielectric_smoothing", False)),
        notes=str(value.get("notes", "")),
        tags=[str(item) for item in value.get("tags", [])],
    )


def _antenna_model_to_payload(antenna: AntennaModelDefinition) -> dict[str, Any]:
    return {
        "identifier": antenna.identifier,
        "library": antenna.library,
        "model_key": antenna.model_key,
        "module_path": antenna.module_path,
        "function_name": antenna.function_name,
        "position_m": _vector_to_payload(antenna.position_m),
        "resolution_m": antenna.resolution_m,
        "rotate90": antenna.rotate90,
        "notes": antenna.notes,
        "tags": list(antenna.tags),
    }


def _antenna_model_from_payload(value: dict[str, Any]) -> AntennaModelDefinition:
    return AntennaModelDefinition(
        identifier=str(value.get("identifier", "")),
        library=str(value.get("library", "")),
        model_key=str(value.get("model_key", "")),
        module_path=str(value.get("module_path", "")),
        function_name=str(value.get("function_name", "")),
        position_m=_vector_from_payload(
            value.get("position_m"),
            default=Vector3(x=0.0, y=0.0, z=0.0),
        ),
        resolution_m=float(value.get("resolution_m", 0.001)),
        rotate90=bool(value.get("rotate90", False)),
        notes=str(value.get("notes", "")),
        tags=[str(item) for item in value.get("tags", [])],
    )
