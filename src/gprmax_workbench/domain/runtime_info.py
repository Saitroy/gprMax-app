from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .capability_status import CapabilityStatus
from .engine_config import EngineConfig


@dataclass(slots=True)
class RuntimeInfo:
    engine: EngineConfig
    app_version: str
    bundled_engine_version: str | None
    gprmax_version: str | None
    settings_path: Path
    logs_directory: Path
    cache_directory: Path
    temp_directory: Path
    capabilities: list[CapabilityStatus] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    is_healthy: bool = False

