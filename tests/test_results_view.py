from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.application.services.results_service import ResultsService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.domain.models import Vector3
from gprmax_workbench.domain.results import (
    OutputFileDescriptor,
    OutputFileKind,
    ReceiverResultSummary,
    ResultMetadata,
    RunResultSummary,
)
from gprmax_workbench.domain.simulation import SimulationRunRecord
from gprmax_workbench.domain.traces import AscanTrace, BscanLoadResult, TraceMetadata
from gprmax_workbench.ui.views.results_view import ResultsView


class _FakeResultRepository:
    def __init__(self, summaries: list[RunResultSummary]) -> None:
        self._summaries = summaries

    def list_run_results(self, project_root: Path):
        return self._summaries


class _FakeTraceService:
    def __init__(self, metadata: ResultMetadata, trace: AscanTrace) -> None:
        self._metadata = metadata
        self._trace = trace

    def load_result_metadata(self, output_file: Path) -> ResultMetadata:
        return self._metadata

    def list_output_components(
        self,
        output_file: Path,
        receiver_id: str | None = None,
    ) -> list[str]:
        if receiver_id is None:
            return self._metadata.available_components
        receiver = next(
            item for item in self._metadata.receivers if item.receiver_id == receiver_id
        )
        return receiver.components

    def load_ascan(
        self,
        output_file: Path,
        receiver_id: str,
        component: str,
    ) -> AscanTrace:
        return self._trace


class _FakeBscanService:
    def load_bscan_if_available(self, run_summary, receiver_id, component):
        return BscanLoadResult(
            available=False,
            message="B-scan unavailable.",
            dataset=None,
        )


class ResultsViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_refresh_project_auto_selects_trace_inputs_and_renders_trace(self) -> None:
        output_path = Path("D:/demo/output/simulation.out")
        summary = _build_run_summary(output_path)
        metadata = ResultMetadata(
            output_file=summary.output_files[0],
            gprmax_version="3.1.7",
            model_title="Demo result",
            iterations=4,
            grid_shape=(100, 1, 1),
            resolution_m=(0.01, 0.01, 0.01),
            dt_s=1e-11,
            src_steps_m=(0.0, 0.0, 0.0),
            rx_steps_m=(0.01, 0.0, 0.0),
            source_count=1,
            receiver_count=1,
            receivers=[
                ReceiverResultSummary(
                    receiver_id="rx1",
                    name="Receiver 1",
                    position_m=Vector3(x=0.1, y=0.0, z=0.0),
                    components=["Ez", "Hx"],
                )
            ],
        )
        trace = AscanTrace(
            metadata=TraceMetadata(
                output_file=output_path,
                receiver_id="rx1",
                receiver_name="Receiver 1",
                component="Ez",
                dt_s=1e-11,
                iterations=4,
            ),
            time_s=[0.0, 1e-11, 2e-11, 3e-11],
            values=[0.0, 0.1, -0.2, 0.3],
        )
        results_service = ResultsService(
            result_repository=_FakeResultRepository([summary]),
            state=AppState(),
        )
        view = ResultsView(
            localization=LocalizationService("ru"),
            results_service=results_service,
            trace_service=_FakeTraceService(metadata, trace),
            bscan_service=_FakeBscanService(),
        )

        view.refresh_project(Path("D:/demo"))

        self.assertEqual(view._receiver_combo.count(), 1)
        self.assertEqual(view._component_combo.count(), 2)
        self.assertEqual(results_service.viewer_state.selected_run_id, "run-1")
        self.assertEqual(results_service.viewer_state.selected_receiver_id, "rx1")
        self.assertEqual(results_service.viewer_state.selected_component, "Ez")
        self.assertEqual(
            view._trace_plot._layout.currentWidget().__class__.__name__,
            "QChartView",
        )


def _build_run_summary(output_path: Path) -> RunResultSummary:
    run_record = SimulationRunRecord(
        run_id="run-1",
        project_root=Path("D:/demo"),
        project_name="Demo",
        status=SimulationStatus.COMPLETED,
        created_at=datetime(2026, 3, 19, tzinfo=UTC),
        working_directory=Path("D:/demo/runs/run-1"),
        input_file=Path("D:/demo/runs/run-1/input/simulation.in"),
        output_directory=Path("D:/demo/runs/run-1/output"),
        stdout_log_path=Path("D:/demo/runs/run-1/logs/stdout.log"),
        stderr_log_path=Path("D:/demo/runs/run-1/logs/stderr.log"),
        combined_log_path=Path("D:/demo/runs/run-1/logs/combined.log"),
        metadata_path=Path("D:/demo/runs/run-1/metadata.json"),
        configuration=SimulationRunConfig(),
    )
    return RunResultSummary(
        run_record=run_record,
        output_files=[
            OutputFileDescriptor(
                path=output_path,
                name=output_path.name,
                kind=OutputFileKind.ASCAN,
                size_bytes=1024,
            )
        ],
    )


if __name__ == "__main__":
    unittest.main()
