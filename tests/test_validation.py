from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.models import (
    GeometryPrimitive,
    MaterialDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
    default_project,
)
from gprmax_workbench.domain.validation import validate_project


class ValidationTests(unittest.TestCase):
    def test_validation_reports_errors_and_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project(name="", root=Path(temp_dir))
            project.model.domain.time_window_s = 0.0
            project.model.materials = [
                MaterialDefinition(
                    identifier="soil",
                    relative_permittivity=4.0,
                    conductivity=0.001,
                ),
                MaterialDefinition(
                    identifier="soil",
                    relative_permittivity=6.0,
                    conductivity=0.002,
                ),
            ]

            validation = validate_project(project)

            self.assertFalse(validation.is_valid)
            self.assertGreaterEqual(len(validation.errors), 2)
            self.assertGreaterEqual(len(validation.warnings), 2)

    def test_validation_reports_cross_reference_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project(name="Validation Demo", root=Path(temp_dir))
            project.model.waveforms = [
                WaveformDefinition(
                    identifier="wf1",
                    kind="ricker",
                    amplitude=1.0,
                    center_frequency_hz=1e9,
                )
            ]
            project.model.sources = [
                SourceDefinition(
                    identifier="tx1",
                    kind="hertzian_dipole",
                    axis="z",
                    position_m=Vector3(2.0, 0.0, 0.0),
                    waveform_id="missing",
                )
            ]
            project.model.geometry = [
                GeometryPrimitive(
                    kind="sphere",
                    material_ids=["missing_material"],
                    parameters={
                        "center_m": {"x": 0.5, "y": 0.5, "z": 0.05},
                        "radius_m": -0.1,
                    },
                )
            ]

            validation = validate_project(project)

            self.assertFalse(validation.is_valid)
            self.assertTrue(
                any("waveform_id" in issue.path for issue in validation.warnings)
            )
            self.assertTrue(
                any("radius_m" in issue.path for issue in validation.errors)
            )

    def test_validation_warns_when_stepped_scan_has_no_trace_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project(name="Bscan Demo", root=Path(temp_dir))
            project.advanced_input_overrides = [
                "#src_steps: 0.002 0 0",
                "#rx_steps: 0.002 0 0",
            ]

            validation = validate_project(project)

            self.assertTrue(
                any(issue.path == "model.scan_trace_count" for issue in validation.warnings)
            )


if __name__ == "__main__":
    unittest.main()
