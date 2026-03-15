from __future__ import annotations

from ...domain.engine_config import EngineConfig, EngineResolution
from ...domain.runtime_info import RuntimeInfo
from ...infrastructure.gprmax.adapter import SubprocessGprMaxAdapter
from .diagnostics_service import DiagnosticsService
from .engine_resolution_service import EngineResolutionService
from .settings_service import SettingsService


class RuntimeService:
    """Owns bundled-first runtime selection and health reporting."""

    def __init__(
        self,
        *,
        settings_service: SettingsService,
        engine_resolution_service: EngineResolutionService,
        diagnostics_service: DiagnosticsService,
        adapter: SubprocessGprMaxAdapter,
    ) -> None:
        self._settings_service = settings_service
        self._engine_resolution_service = engine_resolution_service
        self._diagnostics_service = diagnostics_service
        self._adapter = adapter
        self._resolution: EngineResolution | None = None
        self._runtime_info: RuntimeInfo | None = None

    def refresh(self) -> RuntimeInfo:
        resolution = self._engine_resolution_service.resolve(
            self._settings_service.settings
        )
        self._adapter.configure_engine(resolution.engine)
        info = self._diagnostics_service.runtime_info(resolution)
        self._resolution = resolution
        self._runtime_info = info
        return info

    def runtime_info(self) -> RuntimeInfo:
        return self._runtime_info or self.refresh()

    def current_engine(self) -> EngineConfig:
        return self.runtime_info().engine

    def current_resolution(self) -> EngineResolution:
        if self._resolution is None:
            self.refresh()
        assert self._resolution is not None
        return self._resolution
