from __future__ import annotations

from .models import (
    GeometryPrimitive,
    MaterialDefinition,
    Project,
    ReceiverDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
)

EDITOR_GEOMETRY_KINDS = ("box", "sphere", "cylinder")
EDITOR_SOURCE_KINDS = ("hertzian_dipole", "magnetic_dipole", "voltage_source")
EDITOR_SOURCE_AXES = ("x", "y", "z")
EDITOR_WAVEFORM_KINDS = ("ricker", "gaussian", "gaussiandot", "gaussiandotnorm")


def default_material(index: int) -> MaterialDefinition:
    return MaterialDefinition(
        identifier=f"material_{index}",
        relative_permittivity=4.0,
        conductivity=0.001,
    )


def default_waveform(index: int) -> WaveformDefinition:
    return WaveformDefinition(
        identifier=f"waveform_{index}",
        kind="ricker",
        amplitude=1.0,
        center_frequency_hz=1.5e9,
    )


def default_source(project: Project, index: int) -> SourceDefinition:
    size = project.model.domain.size_m
    waveform_id = project.model.waveforms[0].identifier if project.model.waveforms else ""
    return SourceDefinition(
        identifier=f"source_{index}",
        kind="hertzian_dipole",
        axis="z",
        position_m=Vector3(
            x=min(size.x * 0.4, size.x),
            y=min(size.y * 0.7, size.y),
            z=min(size.z * 0.5, size.z),
        ),
        waveform_id=waveform_id,
    )


def default_receiver(project: Project, index: int) -> ReceiverDefinition:
    size = project.model.domain.size_m
    return ReceiverDefinition(
        identifier=f"receiver_{index}",
        position_m=Vector3(
            x=min(size.x * 0.6, size.x),
            y=min(size.y * 0.7, size.y),
            z=min(size.z * 0.5, size.z),
        ),
        outputs=["Ez"],
    )


def default_geometry(project: Project, index: int, *, kind: str = "box") -> GeometryPrimitive:
    size = project.model.domain.size_m
    default_material_id = (
        project.model.materials[0].identifier if project.model.materials else ""
    )

    if kind == "sphere":
        parameters = {
            "center_m": {
                "x": size.x * 0.5,
                "y": size.y * 0.4,
                "z": max(size.z * 0.5, 0.0),
            },
            "radius_m": min(size.x, size.y, max(size.z, size.x * 0.1)) * 0.15,
        }
    elif kind == "cylinder":
        parameters = {
            "start_m": {
                "x": size.x * 0.5,
                "y": size.y * 0.25,
                "z": 0.0,
            },
            "end_m": {
                "x": size.x * 0.5,
                "y": size.y * 0.25,
                "z": max(size.z * 0.9, size.z),
            },
            "radius_m": min(size.x, size.y, max(size.z, size.x * 0.1)) * 0.08,
        }
    else:
        parameters = {
            "lower_left_m": {
                "x": size.x * 0.2,
                "y": size.y * 0.2,
                "z": 0.0,
            },
            "upper_right_m": {
                "x": size.x * 0.8,
                "y": size.y * 0.5,
                "z": max(size.z * 0.6, size.z),
            },
        }

    return GeometryPrimitive(
        kind=kind,
        label=f"{kind}_{index}",
        material_ids=[default_material_id] if default_material_id else [],
        parameters=parameters,
    )
