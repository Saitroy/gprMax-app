from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class TraceMetadata:
    output_file: Path
    receiver_id: str
    receiver_name: str
    component: str
    dt_s: float
    iterations: int


@dataclass(slots=True)
class AscanTrace:
    metadata: TraceMetadata
    time_s: list[float] = field(default_factory=list)
    values: list[float] = field(default_factory=list)


@dataclass(slots=True)
class BscanDataset:
    receiver_id: str
    receiver_name: str
    component: str
    time_s: list[float] = field(default_factory=list)
    amplitudes: list[list[float]] = field(default_factory=list)
    source_files: list[Path] = field(default_factory=list)
    trace_labels: list[str] = field(default_factory=list)

    @property
    def trace_count(self) -> int:
        return len(self.amplitudes)

    @property
    def sample_count(self) -> int:
        return len(self.time_s)


@dataclass(slots=True)
class BscanLoadResult:
    available: bool
    message: str
    dataset: BscanDataset | None = None
