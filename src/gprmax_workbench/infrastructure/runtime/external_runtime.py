from __future__ import annotations

import sys
from pathlib import Path

from ...domain.engine_config import EngineConfig, EngineMode


class ExternalRuntimeProvider:
    """Builds optional advanced or development fallback runtime candidates."""

    def __init__(self, development_python: Path | None = None) -> None:
        self._development_python = development_python or Path(sys.executable)

    def configured_candidate(self, python_executable: str | None) -> EngineConfig | None:
        if not python_executable:
            return None
        return EngineConfig(
            mode=EngineMode.EXTERNAL,
            python_executable=Path(python_executable).expanduser(),
            source_label="External fallback",
        )

    def development_candidate(self) -> EngineConfig:
        return EngineConfig(
            mode=EngineMode.EXTERNAL,
            python_executable=self._development_python,
            source_label="Development fallback",
        )

