from __future__ import annotations

from pathlib import Path

from ...domain.simulation import SimulationRunRecord
from ...infrastructure.persistence.run_repository import RunRepository


class RunService:
    """Read-oriented access to persisted run history and directories."""

    def __init__(self, run_repository: RunRepository) -> None:
        self._run_repository = run_repository

    def get_run_history(self, project_root: Path) -> list[SimulationRunRecord]:
        return self._run_repository.load_history(project_root)

    def get_run(self, metadata_path: Path) -> SimulationRunRecord:
        return self._run_repository.load(metadata_path)
