from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.domain.simulation import SimulationRunRecord
from gprmax_workbench.infrastructure.results.artifact_locator import ResultArtifactLocator


class ResultArtifactLocatorTests(unittest.TestCase):
    def test_describe_run_discovers_output_and_visualisation_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "runs" / "run-1"
            output_dir = run_dir / "output"
            logs_dir = run_dir / "logs"
            input_dir = run_dir / "input"
            output_dir.mkdir(parents=True)
            logs_dir.mkdir()
            input_dir.mkdir()
            (output_dir / "simulation1.out").write_text("", encoding="utf-8")
            (output_dir / "simulation2.out").write_text("", encoding="utf-8")
            (output_dir / "simulation_merged.out").write_text("", encoding="utf-8")
            (output_dir / "snapshot1.vti").write_text("", encoding="utf-8")

            run_record = SimulationRunRecord(
                run_id="run-1",
                project_root=root,
                project_name="Demo",
                status=SimulationStatus.COMPLETED,
                created_at=datetime(2026, 3, 15, tzinfo=UTC),
                working_directory=run_dir,
                input_file=input_dir / "simulation.in",
                output_directory=output_dir,
                stdout_log_path=logs_dir / "stdout.log",
                stderr_log_path=logs_dir / "stderr.log",
                combined_log_path=logs_dir / "combined.log",
                metadata_path=run_dir / "metadata.json",
                configuration=SimulationRunConfig(),
            )

            summary = ResultArtifactLocator().describe_run(run_record)

            self.assertEqual(len(summary.output_files), 3)
            self.assertTrue(any(item.is_merged for item in summary.output_files))
            self.assertEqual(len(summary.visualisation_artifacts), 1)
            self.assertFalse(summary.issues)


if __name__ == "__main__":
    unittest.main()
