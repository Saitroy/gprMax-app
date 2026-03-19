from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.bscan_service import BscanService
from gprmax_workbench.application.services.results_service import ResultsService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.domain.results import (
    OutputFileDescriptor,
    OutputFileKind,
    RunResultSummary,
)
from gprmax_workbench.domain.simulation import SimulationRunRecord
from gprmax_workbench.domain.traces import AscanTrace, BscanLoadResult, TraceMetadata


class _FakeResultRepository:
    def __init__(self, summaries) -> None:
        self._summaries = summaries

    def list_run_results(self, project_root: Path):
        return self._summaries


class _FakeBscanBuilder:
    def load_bscan(self, run_summary, receiver_id, component):
        return BscanLoadResult(
            available=True,
            message="ok",
            dataset=None,
        )


class ResultsServiceTests(unittest.TestCase):
    def test_refresh_results_sets_default_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            run_summary = _build_run_summary(project_root, "run-1")
            state = AppState()
            service = ResultsService(
                result_repository=_FakeResultRepository([run_summary]),
                state=state,
            )

            results = service.refresh_results(project_root)

            self.assertEqual(len(results), 1)
            self.assertEqual(service.viewer_state.selected_run_id, "run-1")

    def test_select_output_resets_receiver_and_component(self) -> None:
        state = AppState()
        service = ResultsService(
            result_repository=_FakeResultRepository([]),
            state=state,
        )
        state.results_viewer.selected_receiver_id = "rx1"
        state.results_viewer.selected_component = "Ez"
        state.results_viewer.selected_ascan_components = ["Ez", "Hx"]

        service.select_output_file(Path("D:/demo/trace.out"))

        self.assertIsNone(state.results_viewer.selected_receiver_id)
        self.assertIsNone(state.results_viewer.selected_component)
        self.assertEqual(state.results_viewer.selected_ascan_components, [])

    def test_focus_run_resets_dependent_viewer_selection(self) -> None:
        state = AppState()
        service = ResultsService(
            result_repository=_FakeResultRepository([]),
            state=state,
        )
        state.results_viewer.selected_output_file = "D:/demo/trace.out"
        state.results_viewer.selected_receiver_id = "rx1"
        state.results_viewer.selected_component = "Ez"
        state.results_viewer.selected_ascan_components = ["Ez", "Hx"]

        service.focus_run("run-2")

        self.assertEqual(state.results_viewer.selected_run_id, "run-2")
        self.assertIsNone(state.results_viewer.selected_output_file)
        self.assertIsNone(state.results_viewer.selected_receiver_id)
        self.assertIsNone(state.results_viewer.selected_component)
        self.assertEqual(state.results_viewer.selected_ascan_components, [])

    def test_bscan_service_delegates_to_builder(self) -> None:
        service = BscanService(_FakeBscanBuilder())
        result = service.load_bscan_if_available(
            _build_run_summary(Path("D:/demo"), "run-1"),
            "rx1",
            "Ez",
        )
        self.assertTrue(result.available)


def _build_run_summary(project_root: Path, run_id: str) -> RunResultSummary:
    run_dir = project_root / "runs" / run_id
    output_dir = run_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "simulation1.out"
    output_file.write_text("", encoding="utf-8")
    run_record = SimulationRunRecord(
        run_id=run_id,
        project_root=project_root,
        project_name="Demo",
        status=SimulationStatus.COMPLETED,
        created_at=datetime(2026, 3, 15, tzinfo=UTC),
        working_directory=run_dir,
        input_file=run_dir / "input" / "simulation.in",
        output_directory=output_dir,
        stdout_log_path=run_dir / "logs" / "stdout.log",
        stderr_log_path=run_dir / "logs" / "stderr.log",
        combined_log_path=run_dir / "logs" / "combined.log",
        metadata_path=run_dir / "metadata.json",
        configuration=SimulationRunConfig(),
    )
    return RunResultSummary(
        run_record=run_record,
        output_files=[
            OutputFileDescriptor(
                path=output_file,
                name=output_file.name,
                kind=OutputFileKind.ASCAN,
                size_bytes=0,
            )
        ],
    )


if __name__ == "__main__":
    unittest.main()
