from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.input_generation_service import (
    InputGenerationService,
)
from gprmax_workbench.application.services.input_preview_service import InputPreviewService
from gprmax_workbench.application.services.validation_service import ValidationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.models import (
    GeometryPrimitive,
    MaterialDefinition,
    ReceiverDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
    default_project,
)
from gprmax_workbench.infrastructure.gprmax.input_generator import GprMaxInputGenerator
from gprmax_workbench.infrastructure.persistence.artifact_store import RunArtifactStore


class InputPreviewServiceTests(unittest.TestCase):
    def test_generate_preview_uses_current_project_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Preview Demo", Path(temp_dir))
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
                    kind="voltage_source",
                    axis="z",
                    position_m=Vector3(0.1, 0.1, 0.0),
                    waveform_id="wf1",
                    delay_s=1e-9,
                    resistance_ohms=75.0,
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
                    kind="sphere",
                    label="target",
                    material_ids=["soil"],
                    dielectric_smoothing=False,
                    parameters={
                        "center_m": {"x": 0.5, "y": 0.5, "z": 0.05},
                        "radius_m": 0.1,
                    },
                )
            ]

            state = AppState(current_project=project)
            preview_service = InputPreviewService(
                input_generation_service=InputGenerationService(
                    generator=GprMaxInputGenerator(),
                    artifact_store=RunArtifactStore(),
                ),
                validation_service=ValidationService(state),
            )

            preview = preview_service.generate_preview(project)

            self.assertTrue(preview.generated)
            self.assertIn("#voltage_source:", preview.text)
            self.assertIn("75", preview.text)
            self.assertIn("#sphere:", preview.text)
            self.assertIn(" n", preview.text)


if __name__ == "__main__":
    unittest.main()
