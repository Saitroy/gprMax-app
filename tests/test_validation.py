from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.models import MaterialDefinition, default_project
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


if __name__ == "__main__":
    unittest.main()
