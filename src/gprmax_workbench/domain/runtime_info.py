from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .capability_status import CapabilityLevel, CapabilityStatus
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

    def capability(self, code: str) -> CapabilityStatus | None:
        for item in self.capabilities:
            if item.code == code:
                return item
        return None

    def capability_level(self, code: str) -> CapabilityLevel | None:
        capability = self.capability(code)
        return capability.level if capability is not None else None

    def is_capability_ready(self, code: str) -> bool:
        return self.capability_level(code) == CapabilityLevel.READY
