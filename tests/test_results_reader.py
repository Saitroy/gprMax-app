from __future__ import annotations

import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.infrastructure.results.hdf5_reader import (
    Hdf5ResultsReader,
    ResultsReadError,
)


class _FakeDataset:
    def __init__(self, value) -> None:
        self._value = np.asarray(value)

    def __getitem__(self, key):
        if key != ():
            raise KeyError(key)
        return self._value


class _FakeGroup(dict):
    def __init__(self, values=None, *, attrs=None) -> None:
        super().__init__(values or {})
        self.attrs = attrs or {}


class _FakeFile(_FakeGroup):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _TestReader(Hdf5ResultsReader):
    def __init__(self, files: dict[Path, _FakeFile]) -> None:
        self._files = files

    def _open_file(self, path: Path):
        if path not in self._files:
            raise ResultsReadError(f"Missing fake file: {path}")
        return self._files[path]


def _build_fake_result_file(dataset_value) -> _FakeFile:
    return _FakeFile(
        {
            "rxs": _FakeGroup(
                {
                    "rx1": _FakeGroup(
                        {
                            "Ez": _FakeDataset(dataset_value),
                            "Ex": _FakeDataset([0.0, 0.1, 0.2]),
                        },
                        attrs={
                            "Name": b"Receiver 1",
                            "Position": np.asarray([0.1, 0.2, 0.3]),
                        },
                    )
                }
            )
        },
        attrs={
            "gprMax": b"4.0-test",
            "Title": b"Test model",
            "Iterations": 3,
            "nx_ny_nz": np.asarray([50, 60, 10]),
            "dx_dy_dz": np.asarray([0.01, 0.01, 0.01]),
            "dt": 1e-11,
            "srcsteps": np.asarray([0.01, 0.0, 0.0]),
            "rxsteps": np.asarray([0.01, 0.0, 0.0]),
            "nsrc": 1,
            "nrx": 1,
        },
    )


class ResultsReaderTests(unittest.TestCase):
    def test_load_metadata_and_ascan_from_fake_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "trace.out"
            output_path.write_text("", encoding="utf-8")
            reader = _TestReader({output_path: _build_fake_result_file([1.0, -0.5, 0.25])})

            metadata = reader.load_metadata(output_path)
            trace = reader.load_ascan(output_path, "rx1", "Ez")

            self.assertEqual(metadata.gprmax_version, "4.0-test")
            self.assertEqual(metadata.receiver_count, 1)
            self.assertEqual(metadata.available_components, ["Ex", "Ez"])
            self.assertEqual(trace.metadata.receiver_name, "Receiver 1")
            self.assertEqual(trace.values, [1.0, -0.5, 0.25])
            self.assertAlmostEqual(trace.time_s[1], 1e-11)

    def test_load_matrix_from_merged_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "trace_merged.out"
            output_path.write_text("", encoding="utf-8")
            reader = _TestReader(
                {
                    output_path: _build_fake_result_file(
                        np.asarray(
                            [
                                [1.0, 2.0],
                                [3.0, 4.0],
                                [5.0, 6.0],
                            ]
                        )
                    )
                }
            )

            amplitudes, time_s, labels = reader.load_matrix(output_path, "rx1", "Ez")

            self.assertEqual(len(amplitudes), 2)
            self.assertEqual(len(time_s), 3)
            self.assertIn("trace_1", labels)

    def test_missing_h5py_dependency_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "trace.out"
            output_path.write_text("", encoding="utf-8")

            import builtins

            original_import = builtins.__import__

            def raising_import(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "h5py":
                    raise ImportError("h5py unavailable")
                return original_import(name, globals, locals, fromlist, level)

            with patch("builtins.__import__", side_effect=raising_import):
                with self.assertRaises(ResultsReadError) as context:
                    Hdf5ResultsReader().load_metadata(output_path)

            self.assertIn("h5py", str(context.exception))


if __name__ == "__main__":
    unittest.main()
