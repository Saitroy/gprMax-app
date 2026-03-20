from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.models import (
    GeometryPrimitive,
    MaterialDefinition,
    ModelDomain,
    Project,
    ProjectMetadata,
    ProjectModel,
    ReceiverDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
)
from gprmax_workbench.infrastructure.project_store import JsonProjectStore


class JsonProjectStoreTests(unittest.TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = JsonProjectStore()
            project = Project(
                root=root,
                metadata=ProjectMetadata(
                    name="Demo project",
                    description="Roundtrip test",
                    created_at=datetime(2026, 3, 15, tzinfo=UTC),
                    updated_at=datetime(2026, 3, 15, tzinfo=UTC),
                ),
                model=ProjectModel(
                    title="Stage 2 model",
                    scan_trace_count=45,
                    notes="Model notes",
                    tags=["stage4", "editor"],
                    domain=ModelDomain(
                        size_m=Vector3(x=2.0, y=1.5, z=0.2),
                        resolution_m=Vector3(x=0.01, y=0.01, z=0.01),
                        time_window_s=5e-9,
                    ),
                    materials=[
                        MaterialDefinition(
                            identifier="sand",
                            relative_permittivity=4.0,
                            conductivity=0.001,
                            notes="Reference material",
                            tags=["soil"],
                        )
                    ],
                    waveforms=[
                        WaveformDefinition(
                            identifier="wf1",
                            kind="ricker",
                            amplitude=1.0,
                            center_frequency_hz=1e9,
                            notes="Default waveform",
                            tags=["default"],
                        )
                    ],
                    sources=[
                        SourceDefinition(
                            identifier="tx1",
                            kind="hertzian_dipole",
                            axis="z",
                            position_m=Vector3(x=0.1, y=0.1, z=0.0),
                            waveform_id="wf1",
                            delay_s=1e-9,
                            notes="Transmitter",
                            tags=["tx"],
                        )
                    ],
                    receivers=[
                        ReceiverDefinition(
                            identifier="rx1",
                            position_m=Vector3(x=0.2, y=0.1, z=0.0),
                            outputs=["Ez"],
                            notes="Receiver",
                            tags=["rx"],
                        )
                    ],
                    geometry=[
                        GeometryPrimitive(
                            kind="box",
                            label="slab",
                            material_ids=["sand"],
                            dielectric_smoothing=False,
                            notes="Test geometry",
                            tags=["geom"],
                            parameters={
                                "lower_left_m": {"x": 0.0, "y": 0.0, "z": 0.0},
                                "upper_right_m": {"x": 1.0, "y": 1.0, "z": 0.2},
                            },
                        )
                    ],
                    python_blocks=["# python block placeholder"],
                ),
                advanced_input_overrides=["# custom raw command"],
            )

            project_file = store.save(project)
            loaded = store.load(root)

            self.assertTrue(project_file.exists())
            self.assertEqual(loaded.metadata.name, "Demo project")
            self.assertEqual(loaded.model.title, "Stage 2 model")
            self.assertEqual(loaded.model.scan_trace_count, 45)
            self.assertEqual(loaded.model.notes, "Model notes")
            self.assertEqual(loaded.model.tags, ["stage4", "editor"])
            self.assertEqual(loaded.model.domain.size_m.x, 2.0)
            self.assertEqual(loaded.model.materials[0].identifier, "sand")
            self.assertEqual(loaded.model.materials[0].tags, ["soil"])
            self.assertEqual(loaded.model.sources[0].waveform_id, "wf1")
            self.assertEqual(loaded.model.sources[0].delay_s, 1e-9)
            self.assertEqual(loaded.model.receivers[0].outputs, ["Ez"])
            self.assertFalse(loaded.model.geometry[0].dielectric_smoothing)
            self.assertEqual(loaded.model.geometry[0].label, "slab")
            self.assertEqual(loaded.advanced_input_overrides, ["# custom raw command"])


if __name__ == "__main__":
    unittest.main()
