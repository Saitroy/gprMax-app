from __future__ import annotations

from pathlib import Path

from ...domain.results import ResultMetadata, RunResultSummary
from ...domain.traces import AscanTrace
from ..persistence.run_repository import RunRepository
from .artifact_locator import ResultArtifactLocator
from .hdf5_reader import Hdf5ResultsReader


class ResultRepository:
    """Read-oriented repository for run-centric result discovery and HDF5 access."""

    def __init__(
        self,
        *,
        run_repository: RunRepository,
        artifact_locator: ResultArtifactLocator,
        reader: Hdf5ResultsReader,
    ) -> None:
        self._run_repository = run_repository
        self._artifact_locator = artifact_locator
        self._reader = reader

    def list_run_results(self, project_root: Path) -> list[RunResultSummary]:
        history = self._run_repository.load_history(project_root)
        return [self._artifact_locator.describe_run(record) for record in history]

    def describe_run(self, run_record) -> RunResultSummary:
        return self._artifact_locator.describe_run(run_record)

    def load_metadata(self, output_file: Path) -> ResultMetadata:
        return self._reader.load_metadata(output_file)

    def list_receivers(self, output_file: Path):
        return self._reader.list_receivers(output_file)

    def list_components(self, output_file: Path, receiver_id: str | None = None):
        return self._reader.list_components(output_file, receiver_id)

    def load_ascan(
        self,
        output_file: Path,
        receiver_id: str,
        component: str,
    ) -> AscanTrace:
        return self._reader.load_ascan(output_file, receiver_id, component)
