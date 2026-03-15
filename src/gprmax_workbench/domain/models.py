from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


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
    model: dict[str, Any] = field(default_factory=dict)
    advanced_input_overrides: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SimulationRequest:
    project_root: Path
    input_file: Path
    extra_arguments: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SimulationRunRecord:
    run_id: str
    status: RunStatus
    working_directory: Path
    command: list[str]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stdout_log: Path | None = None
    stderr_log: Path | None = None
