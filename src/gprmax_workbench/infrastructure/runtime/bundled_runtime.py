from __future__ import annotations

from ...domain.engine_config import EngineConfig, EngineMode
from .path_manager import PathManager


class BundledRuntimeProvider:
    """Builds the expected bundled-engine candidate from the install layout."""

    def __init__(self, path_manager: PathManager) -> None:
        self._path_manager = path_manager

    def candidate(self) -> EngineConfig:
        return EngineConfig(
            mode=EngineMode.BUNDLED,
            python_executable=self._path_manager.bundled_python_executable(),
            engine_root=self._path_manager.bundled_engine_root,
            installation_root=self._path_manager.installation_root,
            source_label="Bundled engine",
        )

