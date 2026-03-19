from __future__ import annotations

from pathlib import Path

from ...domain.results import RunResultSummary
from ...domain.viewer_state import ResultsViewerState
from ...infrastructure.results.result_repository import ResultRepository
from ..state import AppState


class ResultsService:
    """Coordinates run-centric result discovery and viewer selection state."""

    def __init__(
        self,
        *,
        result_repository: ResultRepository,
        state: AppState,
    ) -> None:
        self._result_repository = result_repository
        self._state = state

    @property
    def viewer_state(self) -> ResultsViewerState:
        return self._state.results_viewer

    def refresh_results(self, project_root: Path | None) -> list[RunResultSummary]:
        if project_root is None:
            self._reset_viewer_state()
            return []

        results = self._result_repository.list_run_results(project_root)
        selected_run_id = self._state.results_viewer.selected_run_id
        if not results:
            self._reset_viewer_state()
            return []

        if selected_run_id not in {item.run_record.run_id for item in results}:
            self._state.results_viewer.selected_run_id = results[0].run_record.run_id
            self._state.results_viewer.selected_output_file = None
            self._state.results_viewer.selected_receiver_id = None
            self._state.results_viewer.selected_component = None
        return results

    def select_run(self, run_id: str | None) -> None:
        self._state.results_viewer.selected_run_id = run_id
        self._state.results_viewer.selected_output_file = None
        self._state.results_viewer.selected_receiver_id = None
        self._state.results_viewer.selected_component = None

    def focus_run(self, run_id: str | None) -> None:
        """Select a run and reset dependent result selections."""
        self.select_run(run_id)

    def select_output_file(self, output_file: Path | None) -> None:
        self._state.results_viewer.selected_output_file = (
            str(output_file) if output_file is not None else None
        )
        self._state.results_viewer.selected_receiver_id = None
        self._state.results_viewer.selected_component = None

    def select_receiver(self, receiver_id: str | None) -> None:
        self._state.results_viewer.selected_receiver_id = receiver_id
        self._state.results_viewer.selected_component = None

    def select_component(self, component: str | None) -> None:
        self._state.results_viewer.selected_component = component

    def selected_output_path(self) -> Path | None:
        raw = self._state.results_viewer.selected_output_file
        if not raw:
            return None
        return Path(raw)

    def open_output_directory(self, run_summary: RunResultSummary | None) -> Path | None:
        if run_summary is None:
            return None
        output_directory = run_summary.run_record.output_directory
        if output_directory.exists():
            return output_directory
        return run_summary.run_record.working_directory if run_summary.run_record.working_directory.exists() else None

    def _reset_viewer_state(self) -> None:
        self._state.results_viewer = ResultsViewerState()
