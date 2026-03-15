from __future__ import annotations

from ...domain.engine_config import EngineResolution
from ...domain.runtime_info import RuntimeInfo
from ...infrastructure.runtime.diagnostics import RuntimeDiagnostics


class DiagnosticsService:
    def __init__(self, diagnostics: RuntimeDiagnostics) -> None:
        self._diagnostics = diagnostics

    def runtime_info(self, resolution: EngineResolution) -> RuntimeInfo:
        return self._diagnostics.inspect(resolution)

