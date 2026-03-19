from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.domain.results import (
    OutputFileDescriptor,
    OutputFileKind,
    RunResultSummary,
)
from gprmax_workbench.domain.simulation import SimulationRunRecord
from gprmax_workbench.domain.traces import AscanTrace, TraceMetadata
from gprmax_workbench.infrastructure.results.bscan_builder import BscanBuilder
from gprmax_workbench.infrastructure.results.hdf5_reader import ResultsReadError


class _FakeTraceReader:
    def __init__(self, traces: dict[Path, AscanTrace]) -> None:
        self._traces = traces

    def load_ascan(self, output_file: Path, receiver_id: str, component: str) -> AscanTrace:
        trace = self._traces.get(output_file)
        if trace is None:
            raise ResultsReadError("Missing trace")
        return trace

    def load_matrix(self, output_file: Path, receiver_id: str, component: str):
        raise ResultsReadError("No merged dataset")

    def load_metadata(self, output_file: Path):
        raise ResultsReadError("Not needed for this test")


class _FakeMatrixReader(_FakeTraceReader):
    def __init__(self, matrix_file: Path) -> None:
        super().__init__({})
        self._matrix_file = matrix_file

    def load_matrix(self, output_file: Path, receiver_id: str, component: str):
        if output_file != self._matrix_file:
            raise ResultsReadError("No merged dataset")
        return (
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            [0.0, 1e-11, 2e-11],
            ["trace_1", "trace_2"],
        )

    def load_metadata(self, output_file: Path):
        from gprmax_workbench.domain.models import Vector3
        from gprmax_workbench.domain.results import ReceiverResultSummary, ResultMetadata

        return ResultMetadata(
            output_file=OutputFileDescriptor(
                path=output_file,
                name=output_file.name,
                kind=OutputFileKind.ASCAN,
                size_bytes=0,
            ),
            gprmax_version="3.1.7",
            model_title="Merged result",
            iterations=3,
            grid_shape=(10, 1, 1),
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
                    position_m=Vector3(x=0.0, y=0.0, z=0.0),
                    components=["Ez"],
                )
            ],
        )


class BscanBuilderTests(unittest.TestCase):
    def test_stacks_multiple_ascan_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            run_dir = project_root / "runs" / "run-1"
            output_dir = run_dir / "output"
            output_dir.mkdir(parents=True)

            trace1_path = output_dir / "trace1.out"
            trace2_path = output_dir / "trace2.out"
            trace1_path.write_text("", encoding="utf-8")
            trace2_path.write_text("", encoding="utf-8")

            summary = RunResultSummary(
                run_record=SimulationRunRecord(
                    run_id="run-1",
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
                ),
                output_files=[
                    OutputFileDescriptor(
                        path=trace1_path,
                        name=trace1_path.name,
                        kind=OutputFileKind.ASCAN,
                        size_bytes=0,
                    ),
                    OutputFileDescriptor(
                        path=trace2_path,
                        name=trace2_path.name,
                        kind=OutputFileKind.ASCAN,
                        size_bytes=0,
                    ),
                ],
            )

            reader = _FakeTraceReader(
                {
                    trace1_path: AscanTrace(
                        metadata=TraceMetadata(
                            output_file=trace1_path,
                            receiver_id="rx1",
                            receiver_name="Receiver 1",
                            component="Ez",
                            dt_s=1e-11,
                            iterations=3,
                        ),
                        time_s=[0.0, 1e-11, 2e-11],
                        values=[1.0, 2.0, 3.0],
                    ),
                    trace2_path: AscanTrace(
                        metadata=TraceMetadata(
                            output_file=trace2_path,
                            receiver_id="rx1",
                            receiver_name="Receiver 1",
                            component="Ez",
                            dt_s=1e-11,
                            iterations=3,
                        ),
                        time_s=[0.0, 1e-11, 2e-11],
                        values=[4.0, 5.0, 6.0],
                    ),
                }
            )

            result = BscanBuilder(reader).load_bscan(summary, "rx1", "Ez")

            self.assertTrue(result.available)
            assert result.dataset is not None
            self.assertEqual(result.dataset.trace_count, 2)
            self.assertEqual(result.dataset.sample_count, 3)
            self.assertEqual(result.dataset.amplitudes[1][2], 6.0)

    def test_uses_matrix_dataset_even_when_file_kind_is_not_marked_merged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            run_dir = project_root / "runs" / "run-1"
            output_dir = run_dir / "output"
            output_dir.mkdir(parents=True)
            matrix_path = output_dir / "survey.out"
            matrix_path.write_text("", encoding="utf-8")

            summary = RunResultSummary(
                run_record=SimulationRunRecord(
                    run_id="run-1",
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
                ),
                output_files=[
                    OutputFileDescriptor(
                        path=matrix_path,
                        name=matrix_path.name,
                        kind=OutputFileKind.ASCAN,
                        size_bytes=1024,
                    )
                ],
            )

            result = BscanBuilder(_FakeMatrixReader(matrix_path)).load_bscan(
                summary,
                "rx1",
                "Ez",
            )

            self.assertTrue(result.available)
            assert result.dataset is not None
            self.assertEqual(result.dataset.trace_count, 2)


if __name__ == "__main__":
    unittest.main()
