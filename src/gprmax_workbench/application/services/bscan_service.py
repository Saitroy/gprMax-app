from __future__ import annotations

from ...domain.results import RunResultSummary
from ...domain.traces import BscanLoadResult
from ...infrastructure.results.bscan_builder import BscanBuilder


class BscanService:
    """Builds bounded B-scan previews for supported result layouts."""

    def __init__(self, builder: BscanBuilder) -> None:
        self._builder = builder

    def load_bscan_if_available(
        self,
        run_summary: RunResultSummary,
        receiver_id: str,
        component: str,
    ) -> BscanLoadResult:
        return self._builder.load_bscan(run_summary, receiver_id, component)
