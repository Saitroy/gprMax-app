from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.models import Project, ProjectMetadata
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
                model={"domain": {"dx": 0.01}},
                advanced_input_overrides={"geometry_only": False},
            )

            project_file = store.save(project)
            loaded = store.load(root)

            self.assertTrue(project_file.exists())
            self.assertEqual(loaded.metadata.name, "Demo project")
            self.assertEqual(loaded.model["domain"]["dx"], 0.01)
            self.assertFalse(loaded.advanced_input_overrides["geometry_only"])


if __name__ == "__main__":
    unittest.main()
