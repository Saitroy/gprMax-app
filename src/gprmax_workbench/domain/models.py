from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_SCHEMA_NAME = "gprmax-workbench-project"
PROJECT_SCHEMA_VERSION = 1
BUILTIN_MATERIAL_IDENTIFIERS = frozenset({"pec", "free_space", "grass", "water"})


@dataclass(slots=True)
class Vector3:
    x: float
    y: float
    z: float


@dataclass(slots=True)
class PmlCells:
    x_min: int = 10
    y_min: int = 10
    z_min: int = 10
    x_max: int = 10
    y_max: int = 10
    z_max: int = 10


@dataclass(slots=True)
class ModelDomain:
    size_m: Vector3 = field(
        default_factory=lambda: Vector3(x=1.0, y=1.0, z=0.1)
    )
    resolution_m: Vector3 = field(
        default_factory=lambda: Vector3(x=0.01, y=0.01, z=0.01)
    )
    time_window_s: float = 3e-9
    pml_cells: PmlCells = field(default_factory=PmlCells)


@dataclass(slots=True)
class MaterialDefinition:
    identifier: str
    relative_permittivity: float
    conductivity: float
    relative_permeability: float = 1.0
    magnetic_loss: float = 0.0
    notes: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WaveformDefinition:
    identifier: str
    kind: str
    amplitude: float
    center_frequency_hz: float
    notes: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SourceDefinition:
    kind: str
    axis: str
    position_m: Vector3
    waveform_id: str
    identifier: str = ""
    delay_s: float = 0.0
    resistance_ohms: float | None = None
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReceiverDefinition:
    position_m: Vector3
    identifier: str = ""
    outputs: list[str] = field(default_factory=list)
    notes: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GeometryPrimitive:
    kind: str
    parameters: dict[str, Any] = field(default_factory=dict)
    material_ids: list[str] = field(default_factory=list)
    label: str = ""
    dielectric_smoothing: bool = True
    notes: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GeometryView:
    lower_left_m: Vector3
    upper_right_m: Vector3
    resolution_m: Vector3
    filename: str
    mode: str = "n"


@dataclass(slots=True)
class ProjectModel:
    title: str
    domain: ModelDomain = field(default_factory=ModelDomain)
    scan_trace_count: int | None = None
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    materials: list[MaterialDefinition] = field(default_factory=list)
    waveforms: list[WaveformDefinition] = field(default_factory=list)
    sources: list[SourceDefinition] = field(default_factory=list)
    receivers: list[ReceiverDefinition] = field(default_factory=list)
    geometry: list[GeometryPrimitive] = field(default_factory=list)
    geometry_views: list[GeometryView] = field(default_factory=list)
    python_blocks: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProjectMetadata:
    name: str
    created_at: datetime
    updated_at: datetime
    description: str = ""


@dataclass(slots=True)
class Project:
    root: Path
    metadata: ProjectMetadata
    model: ProjectModel
    advanced_input_overrides: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RecentProject:
    path: Path
    name: str
    last_opened_at: datetime


def default_project(name: str, root: Path) -> Project:
    timestamp = datetime.now(tz=UTC)
    normalized_name = name.strip() or "Untitled Project"

    return Project(
        root=root,
        metadata=ProjectMetadata(
            name=normalized_name,
            description="",
            created_at=timestamp,
            updated_at=timestamp,
        ),
        model=ProjectModel(title=normalized_name),
        advanced_input_overrides=[],
    )
