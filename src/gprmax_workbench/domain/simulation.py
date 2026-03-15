from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .execution_status import SimulationStatus
from .gprmax_config import SimulationRunConfig

RUN_SCHEMA_NAME = "gprmax-workbench-run"
RUN_SCHEMA_VERSION = 1


@dataclass(slots=True)
class RunArtifacts:
    run_directory: Path
    input_directory: Path
    output_directory: Path
    logs_directory: Path
    metadata_path: Path
    input_file: Path
    stdout_log_path: Path
    stderr_log_path: Path
    combined_log_path: Path


@dataclass(slots=True)
class SimulationRunRecord:
    run_id: str
    project_root: Path
    project_name: str
    status: SimulationStatus
    created_at: datetime
    working_directory: Path
    input_file: Path
    output_directory: Path
    stdout_log_path: Path
    stderr_log_path: Path
    combined_log_path: Path
    metadata_path: Path
    configuration: SimulationRunConfig
    command: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    error_summary: str = ""
    output_files: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is None or self.finished_at is None:
            return None
        return max((self.finished_at - self.started_at).total_seconds(), 0.0)


@dataclass(slots=True)
class PreparedSimulationRun:
    record: SimulationRunRecord
    input_text: str
    preview_text: str
    validation_messages: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SimulationLogSnapshot:
    run_id: str
    combined_text: str
    stdout_text: str
    stderr_text: str
