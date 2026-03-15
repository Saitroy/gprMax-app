from __future__ import annotations

from pathlib import Path

from ...domain.results import ReceiverResultSummary, ResultMetadata
from ...domain.traces import AscanTrace
from ...infrastructure.results.result_repository import ResultRepository


class TraceService:
    """Provides read-oriented result metadata and A-scan access."""

    def __init__(self, result_repository: ResultRepository) -> None:
        self._result_repository = result_repository

    def load_result_metadata(self, output_file: Path) -> ResultMetadata:
        return self._result_repository.load_metadata(output_file)

    def list_receivers(self, output_file: Path) -> list[ReceiverResultSummary]:
        return self._result_repository.list_receivers(output_file)

    def list_output_components(
        self,
        output_file: Path,
        receiver_id: str | None = None,
    ) -> list[str]:
        return self._result_repository.list_components(output_file, receiver_id)

    def load_ascan(
        self,
        output_file: Path,
        receiver_id: str,
        component: str,
    ) -> AscanTrace:
        return self._result_repository.load_ascan(output_file, receiver_id, component)
