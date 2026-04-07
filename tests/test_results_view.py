from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import Qt
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
from gprmax_workbench.domain.traces import (
    AscanTrace,
    BscanDataset,
    BscanLoadResult,
    TraceMetadata,
)
from gprmax_workbench.ui.views.results_view import ResultsView


class _FakeResultRepository:
    def __init__(self, summaries: list[RunResultSummary]) -> None:
        self._summaries = summaries

    def list_run_results(self, project_root: Path):
        return self._summaries


class _FakeTraceService:
    def __init__(self, metadata: ResultMetadata, traces: dict[str, AscanTrace]) -> None:
        self._metadata = metadata
        self._traces = traces

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
        return self._traces[component]

    def load_ascans(
        self,
        output_file: Path,
        receiver_id: str,
        components: list[str],
    ) -> list[AscanTrace]:
        return [self._traces[component] for component in components]


class _FakeBscanService:
    def __init__(self, *, available: bool = False) -> None:
        self._available = available

    def load_bscan_if_available(self, run_summary, receiver_id, component):
        if not self._available:
            return BscanLoadResult(
                available=False,
                message="B-scan unavailable.",
                dataset=None,
            )
        return BscanLoadResult(
            available=True,
            message="Loaded B-scan from merged output file.",
            dataset=BscanDataset(
                receiver_id=receiver_id,
                receiver_name="Receiver 1",
                component=component,
                time_s=[0.0, 1e-11, 2e-11, 3e-11],
                amplitudes=[
                    [0.0, 0.1, -0.1, 0.2],
                    [0.2, 0.0, -0.2, 0.1],
                ],
                trace_labels=["trace-1", "trace-2"],
            ),
        )


class ResultsViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_refresh_project_populates_separate_ascan_controls(self) -> None:
        output_path = Path("D:/demo/output/simulation.out")
        summary = _build_run_summary(output_path)
        metadata = _build_metadata(summary.output_files[0], components=["Ez", "Hx"])
        traces = _build_traces(output_path, components=["Ez", "Hx"])
        view, results_service = _build_view(
            [summary],
            metadata=metadata,
            traces=traces,
        )

        view.refresh_project(Path("D:/demo"))

        self.assertEqual(results_service.viewer_state.selected_run_id, "run-1")
        self.assertEqual(view._ascan_output_combo.count(), 1)
        self.assertEqual(view._ascan_receiver_combo.count(), 1)
        self.assertEqual(view._ascan_component_list.count(), 2)
        self.assertEqual(view._bscan_output_combo.count(), 0)
        self.assertEqual(
            view._trace_plot._layout.currentWidget().__class__.__name__,
            "QChartView",
        )
        self.assertEqual(len(view._trace_plot._chart.series()), 1)

        view._ascan_component_list.item(1).setCheckState(Qt.CheckState.Checked)

        self.assertEqual(len(view._trace_plot._chart.series()), 2)
        self.assertTrue(view._trace_plot._chart.legend().isVisible())

    def test_merged_bscan_run_separates_ascan_and_bscan_controls(self) -> None:
        merged_output = Path("D:/demo/output/simulation_merged.out")
        single_output = Path("D:/demo/output/simulation1.out")
        summary = _build_run_summary(
            merged_output,
            extra_outputs=[
                OutputFileDescriptor(
                    path=single_output,
                    name=single_output.name,
                    kind=OutputFileKind.ASCAN,
                    size_bytes=512,
                )
            ],
            output_kind=OutputFileKind.MERGED,
        )
        metadata = _build_metadata(summary.output_files[0], components=["Ez"])
        traces = _build_traces(single_output, components=["Ez"])
        view, _results_service = _build_view(
            [summary],
            metadata=metadata,
            traces=traces,
            bscan_available=True,
        )

        view.refresh_project(Path("D:/demo"))

        self.assertTrue(view._tabs.isTabEnabled(1))
        self.assertEqual(view._tabs.currentIndex(), 0)
        self.assertEqual(view._ascan_output_combo.count(), 0)
        self.assertIn("A-scan", view._ascan_status_label.text())
        self.assertFalse(view._show_unmerged_checkbox.isHidden())
        self.assertEqual(view._bscan_output_combo.count(), 1)
        self.assertEqual(view._bscan_output_combo.currentData(), str(merged_output))
        self.assertFalse(view._bscan_view._source_pixmap.isNull())

        view._show_unmerged_checkbox.setChecked(True)

        self.assertEqual(view._ascan_output_combo.count(), 1)
        self.assertEqual(view._ascan_output_combo.currentData(), str(single_output))

        view._tabs.setCurrentIndex(1)
        view._tabs.setCurrentIndex(0)
        view._tabs.setCurrentIndex(1)

        self.assertEqual(view._bscan_output_combo.currentData(), str(merged_output))
        self.assertFalse(view._bscan_view._source_pixmap.isNull())

    def test_stacked_bscan_entry_is_separate_from_ascan_traces(self) -> None:
        output_one = Path("D:/demo/output/simulation1.out")
        output_two = Path("D:/demo/output/simulation2.out")
        summary = _build_run_summary(
            output_one,
            extra_outputs=[
                OutputFileDescriptor(
                    path=output_two,
                    name=output_two.name,
                    kind=OutputFileKind.ASCAN,
                    size_bytes=512,
                )
            ],
        )
        metadata = _build_metadata(summary.output_files[0], components=["Ez"])
        traces = _build_traces(output_one, components=["Ez"])
        view, _results_service = _build_view(
            [summary],
            metadata=metadata,
            traces=traces,
            bscan_available=True,
        )

        view.refresh_project(Path("D:/demo"))

        self.assertEqual(view._ascan_output_combo.count(), 2)
        self.assertTrue(view._show_unmerged_checkbox.isHidden())
        self.assertEqual(view._bscan_output_combo.count(), 1)
        self.assertIn("B-scan", view._bscan_output_combo.currentText())

    def test_refresh_project_respects_focused_run_even_when_result_list_is_unchanged(self) -> None:
        summary_one = _build_run_summary(Path("D:/demo/output/run1.out"), run_id="run-1")
        summary_two = _build_run_summary(Path("D:/demo/output/run2.out"), run_id="run-2")
        metadata = _build_metadata(summary_two.output_files[0], components=["Ez"])
        traces = _build_traces(summary_two.output_files[0].path, components=["Ez"])
        view, results_service = _build_view(
            [summary_two, summary_one],
            metadata=metadata,
            traces=traces,
        )

        view.refresh_project(Path("D:/demo"))
        results_service.focus_run("run-1")
        view.refresh_project(Path("D:/demo"))

        self.assertEqual(results_service.viewer_state.selected_run_id, "run-1")
        self.assertEqual(view._run_list.currentItem().data(Qt.ItemDataRole.UserRole), "run-1")

    def test_standard_desktop_width_keeps_results_splitter_horizontal(self) -> None:
        summary = _build_run_summary(Path("D:/demo/output/run1.out"))
        metadata = _build_metadata(summary.output_files[0], components=["Ez"])
        traces = _build_traces(summary.output_files[0].path, components=["Ez"])
        view, _results_service = _build_view(
            [summary],
            metadata=metadata,
            traces=traces,
        )

        view.resize(1040, 720)
        view.show()
        self._app.processEvents()

        self.assertEqual(view._bottom_splitter.orientation(), Qt.Orientation.Horizontal)  # noqa: SLF001
        self.assertGreaterEqual(view._bottom_splitter.handleWidth(), 10)  # noqa: SLF001
        self.assertGreaterEqual(view._page_splitter.handleWidth(), 10)  # noqa: SLF001


def _build_view(
    summaries: list[RunResultSummary],
    *,
    metadata: ResultMetadata,
    traces: dict[str, AscanTrace],
    bscan_available: bool = False,
) -> tuple[ResultsView, ResultsService]:
    results_service = ResultsService(
        result_repository=_FakeResultRepository(summaries),
        state=AppState(),
    )
    view = ResultsView(
        localization=LocalizationService("ru"),
        results_service=results_service,
        trace_service=_FakeTraceService(metadata, traces),
        bscan_service=_FakeBscanService(available=bscan_available),
    )
    return view, results_service


def _build_metadata(
    output_file: OutputFileDescriptor,
    *,
    components: list[str],
) -> ResultMetadata:
    return ResultMetadata(
        output_file=output_file,
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
                components=components,
            )
        ],
    )


def _build_traces(
    output_path: Path,
    *,
    components: list[str],
) -> dict[str, AscanTrace]:
    traces: dict[str, AscanTrace] = {}
    base_values = {
        "Ez": [0.0, 0.1, -0.2, 0.3],
        "Hx": [0.3, 0.2, -0.1, 0.0],
        "Hy": [0.1, -0.1, 0.2, -0.2],
    }
    for component in components:
        traces[component] = AscanTrace(
            metadata=TraceMetadata(
                output_file=output_path,
                receiver_id="rx1",
                receiver_name="Receiver 1",
                component=component,
                dt_s=1e-11,
                iterations=4,
            ),
            time_s=[0.0, 1e-11, 2e-11, 3e-11],
            values=base_values.get(component, [0.0, 0.0, 0.0, 0.0]),
        )
    return traces


def _build_run_summary(
    output_path: Path,
    *,
    run_id: str = "run-1",
    output_kind: OutputFileKind = OutputFileKind.ASCAN,
    extra_outputs: list[OutputFileDescriptor] | None = None,
) -> RunResultSummary:
    run_record = SimulationRunRecord(
        run_id=run_id,
        project_root=Path("D:/demo"),
        project_name="Demo",
        status=SimulationStatus.COMPLETED,
        created_at=datetime(2026, 3, 19, tzinfo=UTC),
        working_directory=Path(f"D:/demo/runs/{run_id}"),
        input_file=Path(f"D:/demo/runs/{run_id}/input/simulation.in"),
        output_directory=Path(f"D:/demo/runs/{run_id}/output"),
        stdout_log_path=Path(f"D:/demo/runs/{run_id}/logs/stdout.log"),
        stderr_log_path=Path(f"D:/demo/runs/{run_id}/logs/stderr.log"),
        combined_log_path=Path(f"D:/demo/runs/{run_id}/logs/combined.log"),
        metadata_path=Path(f"D:/demo/runs/{run_id}/metadata.json"),
        configuration=SimulationRunConfig(),
    )
    return RunResultSummary(
        run_record=run_record,
        output_files=[
            OutputFileDescriptor(
                path=output_path,
                name=output_path.name,
                kind=output_kind,
                size_bytes=1024,
            )
        ]
        + list(extra_outputs or []),
    )


if __name__ == "__main__":
    unittest.main()
