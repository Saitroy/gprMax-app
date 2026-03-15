from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EngineMode(str, Enum):
    BUNDLED = "bundled"
    EXTERNAL = "external"


@dataclass(slots=True)
class EngineConfig:
    mode: EngineMode
    python_executable: Path
    module_name: str = "gprMax"
    engine_root: Path | None = None
    installation_root: Path | None = None
    source_label: str = ""

    def command_label(self) -> str:
        return f"{self.python_executable} -m {self.module_name}"

    def runtime_label(self) -> str:
        if self.source_label:
            return f"{self.source_label} | {self.command_label()}"
        return self.command_label()


@dataclass(slots=True)
class EngineResolution:
    engine: EngineConfig
    notes: list[str] = field(default_factory=list)

