from __future__ import annotations

from enum import StrEnum


class SimulationStatus(StrEnum):
    PENDING = "pending"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationMode(StrEnum):
    NORMAL = "normal"
    GEOMETRY_ONLY = "geometry_only"
