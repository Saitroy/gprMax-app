from __future__ import annotations

from pathlib import Path

from ...domain.results import RunResultSummary
from ...domain.traces import BscanDataset, BscanLoadResult
from .hdf5_reader import Hdf5ResultsReader, ResultsReadError


class BscanBuilder:
    """Builds bounded B-scan previews from merged files or stacked A-scan outputs."""

    def __init__(self, reader: Hdf5ResultsReader) -> None:
        self._reader = reader

    def load_bscan(
        self,
        run_summary: RunResultSummary,
        receiver_id: str,
        component: str,
    ) -> BscanLoadResult:
        if not run_summary.output_files:
            return BscanLoadResult(False, "No output files are available for this run.")

        merged_result = self._load_matrix_candidate(
            run_summary=run_summary,
            receiver_id=receiver_id,
            component=component,
        )
        if merged_result is not None:
            return merged_result

        single_trace_files = [item for item in run_summary.output_files if not item.is_merged]
        if len(single_trace_files) < 2:
            return BscanLoadResult(
                False,
                "B-scan preview requires either a merged output file or at least two individual .out traces.",
            )

        return self._stack_single_trace_outputs(
            source_files=[item.path for item in single_trace_files],
            receiver_id=receiver_id,
            component=component,
        )

    def _stack_single_trace_outputs(
        self,
        *,
        source_files: list[Path],
        receiver_id: str,
        component: str,
    ) -> BscanLoadResult:
        amplitudes: list[list[float]] = []
        trace_labels: list[str] = []
        reference_time: list[float] | None = None
        receiver_name = receiver_id
        first_error: ResultsReadError | None = None

        for path in source_files:
            try:
                trace = self._reader.load_ascan(path, receiver_id, component)
            except ResultsReadError as exc:
                if first_error is None:
                    first_error = exc
                continue

            if reference_time is None:
                reference_time = trace.time_s
                receiver_name = trace.metadata.receiver_name
            elif len(reference_time) != len(trace.time_s):
                return BscanLoadResult(
                    False,
                    "B-scan preview is unavailable because the trace lengths are inconsistent across output files.",
                )

            amplitudes.append(trace.values)
            trace_labels.append(path.stem)

        if len(amplitudes) < 2 or reference_time is None:
            if first_error is not None and not amplitudes:
                return BscanLoadResult(False, str(first_error))
            return BscanLoadResult(
                False,
                "B-scan preview is unavailable for the selected receiver/component in this run.",
            )

        return BscanLoadResult(
            available=True,
            message="Built B-scan preview by stacking individual output files.",
            dataset=BscanDataset(
                receiver_id=receiver_id,
                receiver_name=receiver_name,
                component=component,
                time_s=reference_time,
                amplitudes=amplitudes,
                source_files=source_files,
                trace_labels=trace_labels,
            ),
        )

    def _load_matrix_candidate(
        self,
        *,
        run_summary: RunResultSummary,
        receiver_id: str,
        component: str,
    ) -> BscanLoadResult | None:
        candidates = sorted(
            run_summary.output_files,
            key=lambda item: (0 if item.is_merged else 1, -item.size_bytes, item.name.lower()),
        )
        for output_file in candidates:
            try:
                amplitudes, time_s, trace_labels_raw = self._reader.load_matrix(
                    output_file.path,
                    receiver_id,
                    component,
                )
            except ResultsReadError:
                continue

            metadata = self._reader.load_metadata(output_file.path)
            receiver = next(
                (
                    item
                    for item in metadata.receivers
                    if item.receiver_id == receiver_id
                ),
                None,
            )
            return BscanLoadResult(
                available=True,
                message="Loaded B-scan from merged output file.",
                dataset=BscanDataset(
                    receiver_id=receiver_id,
                    receiver_name=receiver.name if receiver is not None else receiver_id,
                    component=component,
                    time_s=time_s,
                    amplitudes=amplitudes,
                    source_files=[output_file.path],
                    trace_labels=trace_labels_raw,
                ),
            )
        return None
