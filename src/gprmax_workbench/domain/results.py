from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from .models import Vector3
from .simulation import SimulationRunRecord


class OutputFileKind(StrEnum):
    ASCAN = "ascan"
    MERGED = "merged"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class OutputFileDescriptor:
    path: Path
    name: str
    kind: OutputFileKind
    size_bytes: int

    @property
    def is_merged(self) -> bool:
        return self.kind == OutputFileKind.MERGED


@dataclass(slots=True)
class ReceiverResultSummary:
    receiver_id: str
    name: str
    position_m: Vector3
    components: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ResultMetadata:
    output_file: OutputFileDescriptor
    gprmax_version: str
    model_title: str
    iterations: int
    grid_shape: tuple[int, int, int]
    resolution_m: tuple[float, float, float]
    dt_s: float
    src_steps_m: tuple[float, float, float]
    rx_steps_m: tuple[float, float, float]
    source_count: int
    receiver_count: int
    receivers: list[ReceiverResultSummary] = field(default_factory=list)

    @property
    def available_components(self) -> list[str]:
        values = {
            component
            for receiver in self.receivers
            for component in receiver.components
        }
        return sorted(values)


@dataclass(slots=True)
class RunResultSummary:
    run_record: SimulationRunRecord
    output_files: list[OutputFileDescriptor] = field(default_factory=list)
    visualisation_artifacts: list[Path] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def merged_output_files(self) -> list[OutputFileDescriptor]:
        return [item for item in self.output_files if item.is_merged]

    @property
    def individual_output_files(self) -> list[OutputFileDescriptor]:
        return [item for item in self.output_files if not item.is_merged]

    @property
    def supports_bscan_preview(self) -> bool:
        return bool(self.merged_output_files) or len(self.individual_output_files) >= 2

    @property
    def primary_output_file(self) -> OutputFileDescriptor | None:
        if not self.output_files:
            return None
        merged = next((item for item in self.merged_output_files), None)
        return merged or self.output_files[0]
