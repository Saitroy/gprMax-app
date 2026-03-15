from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.project_service import ProjectDraft, ProjectService
from gprmax_workbench.application.services.settings_service import SettingsService
from gprmax_workbench.domain.models import Vector3
from gprmax_workbench.infrastructure.project_store import JsonProjectStore
from gprmax_workbench.infrastructure.settings import SettingsManager


class ProjectServiceTests(unittest.TestCase):
    def test_create_edit_save_and_open_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "demo-project"
            settings_manager = SettingsManager(
                app_name="gprmax_workbench_test",
                base_dir=Path(temp_dir) / "settings",
            )
            settings_service = SettingsService(settings_manager)
            service = ProjectService(
                project_store=JsonProjectStore(),
                settings_service=settings_service,
            )

            project = service.create_project(root=root, name="Demo")
            validation = service.apply_draft(
                project,
                ProjectDraft(
                    project_name="Demo Updated",
                    description="Edited in test",
                    model_title="Primary model",
                    domain_size_m=Vector3(x=3.0, y=2.0, z=0.5),
                    resolution_m=Vector3(x=0.02, y=0.02, z=0.02),
                    time_window_s=6e-9,
                ),
            )
            service.save_project(project)
            reopened = service.open_project(root)

            self.assertTrue(validation.is_valid)
            self.assertTrue((root / "generated").exists())
            self.assertTrue((root / "project.gprwb.json").exists())
            self.assertEqual(reopened.metadata.name, "Demo Updated")
            self.assertEqual(reopened.model.domain.size_m.x, 3.0)
            self.assertEqual(settings_service.recent_projects()[0].name, "Demo Updated")


if __name__ == "__main__":
    unittest.main()
