from __future__ import annotations

from ...domain.engine_config import EngineResolution
from ..settings import AppSettings
from .bundled_runtime import BundledRuntimeProvider
from .external_runtime import ExternalRuntimeProvider


class EngineLocator:
    """Selects the default bundled engine with optional advanced fallback."""

    def __init__(
        self,
        *,
        bundled_provider: BundledRuntimeProvider,
        external_provider: ExternalRuntimeProvider,
    ) -> None:
        self._bundled_provider = bundled_provider
        self._external_provider = external_provider

    def resolve(self, settings: AppSettings) -> EngineResolution:
        notes: list[str] = []
        bundled = self._bundled_provider.candidate()
        if bundled.python_executable.exists():
            notes.append("Using bundled engine from the installation directory.")
            return EngineResolution(engine=bundled, notes=notes)

        notes.append(
            f"Bundled engine was not found at expected path: {bundled.python_executable}"
        )

        if settings.advanced_mode:
            external = self._external_provider.configured_candidate(
                settings.gprmax_python_executable
            )
            if external is not None:
                notes.append("Using configured external fallback runtime.")
                return EngineResolution(engine=external, notes=notes)

        notes.append("Using current Python interpreter as a development fallback.")
        return EngineResolution(
            engine=self._external_provider.development_candidate(),
            notes=notes,
        )

