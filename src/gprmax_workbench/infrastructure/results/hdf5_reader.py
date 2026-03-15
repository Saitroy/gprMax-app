from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import numpy as np

from ...domain.models import Vector3
from ...domain.results import (
    OutputFileDescriptor,
    OutputFileKind,
    ReceiverResultSummary,
    ResultMetadata,
)
from ...domain.traces import AscanTrace, TraceMetadata


class ResultsReadError(RuntimeError):
    """Raised when a result file cannot be opened or parsed."""


class Hdf5ResultsReader:
    """Reads gprMax HDF5 result files without exposing file internals to the UI."""

    def load_metadata(self, output_file: Path) -> ResultMetadata:
        descriptor = OutputFileDescriptor(
            path=output_file,
            name=output_file.name,
            kind=OutputFileKind.MERGED
            if output_file.stem.lower().endswith("_merged")
            else OutputFileKind.ASCAN,
            size_bytes=output_file.stat().st_size if output_file.exists() else 0,
        )

        with self._open_file(output_file) as handle:
            root_attrs = handle.attrs
            receivers = self._read_receivers(handle)
            return ResultMetadata(
                output_file=descriptor,
                gprmax_version=self._string_attr(root_attrs, "gprMax"),
                model_title=self._string_attr(root_attrs, "Title"),
                iterations=self._int_attr(root_attrs, "Iterations"),
                grid_shape=(
                    self._int_attr(root_attrs, "nx_ny_nz", index=0),
                    self._int_attr(root_attrs, "nx_ny_nz", index=1),
                    self._int_attr(root_attrs, "nx_ny_nz", index=2),
                ),
                resolution_m=(
                    self._float_attr(root_attrs, "dx_dy_dz", index=0),
                    self._float_attr(root_attrs, "dx_dy_dz", index=1),
                    self._float_attr(root_attrs, "dx_dy_dz", index=2),
                ),
                dt_s=self._float_attr(root_attrs, "dt"),
                src_steps_m=(
                    self._float_attr(root_attrs, "srcsteps", index=0),
                    self._float_attr(root_attrs, "srcsteps", index=1),
                    self._float_attr(root_attrs, "srcsteps", index=2),
                ),
                rx_steps_m=(
                    self._float_attr(root_attrs, "rxsteps", index=0),
                    self._float_attr(root_attrs, "rxsteps", index=1),
                    self._float_attr(root_attrs, "rxsteps", index=2),
                ),
                source_count=self._int_attr(root_attrs, "nsrc"),
                receiver_count=self._int_attr(root_attrs, "nrx"),
                receivers=receivers,
            )

    def list_receivers(self, output_file: Path) -> list[ReceiverResultSummary]:
        with self._open_file(output_file) as handle:
            return self._read_receivers(handle)

    def list_components(
        self,
        output_file: Path,
        receiver_id: str | None = None,
    ) -> list[str]:
        receivers = self.list_receivers(output_file)
        if receiver_id is None:
            values = {
                component
                for receiver in receivers
                for component in receiver.components
            }
            return sorted(values)

        receiver = next(
            (item for item in receivers if item.receiver_id == receiver_id),
            None,
        )
        return list(receiver.components) if receiver is not None else []

    def load_ascan(
        self,
        output_file: Path,
        receiver_id: str,
        component: str,
    ) -> AscanTrace:
        metadata = self.load_metadata(output_file)
        receiver = next(
            (item for item in metadata.receivers if item.receiver_id == receiver_id),
            None,
        )
        if receiver is None:
            raise ResultsReadError(f"Receiver '{receiver_id}' was not found in {output_file}.")
        if component not in receiver.components:
            raise ResultsReadError(
                f"Component '{component}' is not available for receiver '{receiver_id}'."
            )

        with self._open_file(output_file) as handle:
            try:
                dataset = handle["rxs"][receiver_id][component]
            except Exception as exc:  # pragma: no cover - defensive h5py access
                raise ResultsReadError(
                    f"Dataset rxs/{receiver_id}/{component} is missing."
                ) from exc

            values = self._dataset_to_array(dataset)
            if values.ndim != 1:
                raise ResultsReadError(
                    "Selected dataset is not a 1D A-scan trace. Choose an individual output file for A-scan view."
                )

        time_s = (np.arange(values.shape[0], dtype=float) * metadata.dt_s).tolist()
        return AscanTrace(
            metadata=TraceMetadata(
                output_file=output_file,
                receiver_id=receiver.receiver_id,
                receiver_name=receiver.name,
                component=component,
                dt_s=metadata.dt_s,
                iterations=metadata.iterations,
            ),
            time_s=time_s,
            values=values.astype(float).tolist(),
        )

    def load_matrix(
        self,
        output_file: Path,
        receiver_id: str,
        component: str,
    ) -> tuple[list[list[float]], list[float], list[str]]:
        metadata = self.load_metadata(output_file)
        receiver = next(
            (item for item in metadata.receivers if item.receiver_id == receiver_id),
            None,
        )
        if receiver is None:
            raise ResultsReadError(f"Receiver '{receiver_id}' was not found in {output_file}.")
        if component not in receiver.components:
            raise ResultsReadError(
                f"Component '{component}' is not available for receiver '{receiver_id}'."
            )

        with self._open_file(output_file) as handle:
            dataset = handle["rxs"][receiver_id][component]
            values = self._dataset_to_array(dataset)

        if values.ndim != 2:
            raise ResultsReadError("Selected dataset is not a merged B-scan matrix.")

        samples_axis = 0 if values.shape[0] == metadata.iterations else 1
        if samples_axis == 0:
            oriented = values.T
        else:
            oriented = values
        time_s = (np.arange(oriented.shape[1], dtype=float) * metadata.dt_s).tolist()
        trace_labels = [f"trace_{index + 1}" for index in range(oriented.shape[0])]
        return oriented.astype(float).tolist(), time_s, trace_labels

    def _read_receivers(self, handle: Any) -> list[ReceiverResultSummary]:
        try:
            receivers_group = handle["rxs"]
        except Exception as exc:  # pragma: no cover - defensive h5py access
            raise ResultsReadError("Result file does not contain the 'rxs' group.") from exc

        receivers: list[ReceiverResultSummary] = []
        for receiver_id in sorted(receivers_group.keys()):
            group = receivers_group[receiver_id]
            attrs = getattr(group, "attrs", {})
            receivers.append(
                ReceiverResultSummary(
                    receiver_id=receiver_id,
                    name=self._decode(attrs.get("Name", receiver_id)),
                    position_m=Vector3(
                        x=self._float_from_arrayish(attrs.get("Position"), 0),
                        y=self._float_from_arrayish(attrs.get("Position"), 1),
                        z=self._float_from_arrayish(attrs.get("Position"), 2),
                    ),
                    components=sorted(group.keys()),
                )
            )
        return receivers

    def _open_file(self, path: Path) -> AbstractContextManager[Any]:
        if not path.exists():
            raise ResultsReadError(f"Result file does not exist: {path}")

        try:
            import h5py
        except ImportError as exc:
            raise ResultsReadError(
                "Results viewing requires the 'h5py' package. Install the project dependencies or run the app in the same Python environment as gprMax."
            ) from exc

        try:
            return h5py.File(path, "r")
        except OSError as exc:
            raise ResultsReadError(f"Could not open HDF5 result file: {path}") from exc

    def _string_attr(self, attrs: Any, key: str) -> str:
        return self._decode(attrs.get(key, ""))

    def _int_attr(self, attrs: Any, key: str, *, index: int | None = None) -> int:
        raw = attrs.get(key, 0)
        if index is None:
            return int(np.asarray(raw).reshape(-1)[0]) if np.asarray(raw).size else 0
        return int(np.asarray(raw).reshape(-1)[index]) if np.asarray(raw).size else 0

    def _float_attr(self, attrs: Any, key: str, *, index: int | None = None) -> float:
        raw = attrs.get(key, 0.0)
        if index is None:
            return float(np.asarray(raw).reshape(-1)[0]) if np.asarray(raw).size else 0.0
        return float(np.asarray(raw).reshape(-1)[index]) if np.asarray(raw).size else 0.0

    def _decode(self, value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, np.ndarray) and value.size == 1:
            return self._decode(value.reshape(-1)[0])
        return str(value)

    def _float_from_arrayish(self, value: Any, index: int) -> float:
        array = np.asarray(value if value is not None else [0.0, 0.0, 0.0], dtype=float)
        flattened = array.reshape(-1)
        if flattened.size <= index:
            return 0.0
        return float(flattened[index])

    def _dataset_to_array(self, dataset: Any) -> np.ndarray:
        try:
            return np.asarray(dataset[()], dtype=float)
        except Exception as exc:  # pragma: no cover - defensive h5py access
            raise ResultsReadError("Could not read dataset values.") from exc
