from __future__ import annotations

from ...domain.engine_config import EngineResolution
from ...infrastructure.runtime.engine_locator import EngineLocator
from ...infrastructure.settings import AppSettings


class EngineResolutionService:
    def __init__(self, locator: EngineLocator) -> None:
        self._locator = locator

    def resolve(self, settings: AppSettings) -> EngineResolution:
        return self._locator.resolve(settings)

