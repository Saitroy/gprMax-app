from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.domain.models import (
    GeometryPrimitive,
    GeometryView,
    MaterialDefinition,
    ReceiverDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
    default_project,
)
from gprmax_workbench.infrastructure.gprmax.input_generator import GprMaxInputGenerator


class InputGeneratorTests(unittest.TestCase):
    def test_generates_minimum_supported_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Generator Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(
                    identifier="soil",
                    relative_permittivity=4.0,
                    conductivity=0.001,
                )
            ]
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
                    position_m=Vector3(0.1, 0.1, 0.0),
                    waveform_id="wf1",
                )
            ]
            project.model.receivers = [
                ReceiverDefinition(
                    identifier="rx1",
                    position_m=Vector3(0.2, 0.1, 0.0),
                    outputs=["Ez"],
                )
            ]
            project.model.geometry = [
                GeometryPrimitive(
                    kind="box",
                    material_ids=["soil"],
                    parameters={
                        "lower_left_m": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "upper_right_m": {"x": 1.0, "y": 0.5, "z": 0.1},
                    },
                )
            ]
            project.model.geometry_views = [
                GeometryView(
                    lower_left_m=Vector3(0.0, 0.0, 0.0),
                    upper_right_m=Vector3(1.0, 0.5, 0.1),
                    resolution_m=Vector3(0.01, 0.01, 0.01),
                    filename="geom",
                )
            ]

            generated = GprMaxInputGenerator().generate(
                project=project,
                configuration=SimulationRunConfig(),
                output_dir="../output",
            )

            self.assertIn("#domain:", generated.text)
            self.assertIn("#dx_dy_dz:", generated.text)
            self.assertIn("#material:", generated.text)
            self.assertIn("#waveform:", generated.text)
            self.assertIn("#hertzian_dipole:", generated.text)
            self.assertIn("#rx:", generated.text)
            self.assertIn("#box:", generated.text)
            self.assertIn("#geometry_view:", generated.text)
            self.assertIn("#output_dir: ../output", generated.text)
            self.assertTrue(generated.warnings)


if __name__ == "__main__":
    unittest.main()
