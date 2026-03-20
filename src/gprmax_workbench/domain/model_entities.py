from __future__ import annotations

from .models import (
    AntennaModelDefinition,
    GeometryImportDefinition,
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
EDITOR_COMMAND_CATEGORIES = (
    "general",
    "materials",
    "objects",
    "sources",
    "outputs",
    "pml",
    "advanced",
)

ANTENNA_LIBRARY_CATALOG: dict[str, dict[str, dict[str, str | float | tuple[float, ...]]]] = {
    "gprmax_user_libs": {
        "gssi_1500": {
            "label": "GSSI 1.5 GHz",
            "module_path": "user_libs.antennas.GSSI",
            "function_name": "antenna_like_GSSI_1500",
            "resolution_m": 0.001,
            "manufacturer": "GSSI-like",
            "description": "Shielded antenna model suitable for high-resolution shallow surveys.",
            "dimensions_mm": "170 x 108 x 44",
            "supported_resolutions_m": (0.001,),
        },
        "gssi_400": {
            "label": "GSSI 400 MHz",
            "module_path": "user_libs.antennas.GSSI",
            "function_name": "antenna_like_GSSI_400",
            "resolution_m": 0.001,
            "manufacturer": "GSSI-like",
            "description": "Lower-frequency antenna model with deeper penetration and larger footprint.",
            "dimensions_mm": "340 x 210 x 95",
            "supported_resolutions_m": (0.001,),
        },
        "mala_1200": {
            "label": "MALA 1.2 GHz",
            "module_path": "user_libs.antennas.MALA",
            "function_name": "antenna_like_MALA_1200",
            "resolution_m": 0.001,
            "manufacturer": "MALA-like",
            "description": "Compact antenna model for shallow, high-detail surveys.",
            "dimensions_mm": "150 x 90 x 40",
            "supported_resolutions_m": (0.001,),
        },
    }
}


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


def default_geometry_import(index: int) -> GeometryImportDefinition:
    return GeometryImportDefinition(
        identifier=f"geometry_import_{index}",
        position_m=Vector3(x=0.0, y=0.0, z=0.0),
        geometry_hdf5="",
        materials_file="",
        dielectric_smoothing=False,
    )


def default_antenna_model(project: Project, index: int) -> AntennaModelDefinition:
    size = project.model.domain.size_m
    catalog = ANTENNA_LIBRARY_CATALOG["gprmax_user_libs"]["gssi_1500"]
    return AntennaModelDefinition(
        identifier=f"antenna_{index}",
        library="gprmax_user_libs",
        model_key="gssi_1500",
        module_path=str(catalog["module_path"]),
        function_name=str(catalog["function_name"]),
        position_m=Vector3(
            x=min(size.x * 0.5, size.x),
            y=min(size.y * 0.5, size.y),
            z=min(size.z * 0.1, size.z),
        ),
        resolution_m=float(catalog["resolution_m"]),
    )


def antenna_catalog_entry(
    library: str,
    model_key: str,
) -> dict[str, str | float | tuple[float, ...]] | None:
    return ANTENNA_LIBRARY_CATALOG.get(library, {}).get(model_key)
