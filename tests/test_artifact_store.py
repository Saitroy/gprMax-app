from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.simulation import RunArtifacts
from gprmax_workbench.infrastructure.persistence.artifact_store import RunArtifactStore


class RunArtifactStoreTests(unittest.TestCase):
    def test_list_output_files_includes_gprmax_input_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "runs" / "run-1"
            artifacts = RunArtifacts(
                run_directory=run_dir,
                input_directory=run_dir / "input",
                output_directory=run_dir / "output",
                logs_directory=run_dir / "logs",
                metadata_path=run_dir / "metadata.json",
                input_file=run_dir / "input" / "simulation.in",
                stdout_log_path=run_dir / "logs" / "stdout.log",
                stderr_log_path=run_dir / "logs" / "stderr.log",
                combined_log_path=run_dir / "logs" / "combined.log",
            )
            (artifacts.input_directory / "output").mkdir(parents=True)
            (artifacts.output_directory).mkdir(parents=True)
            (artifacts.input_directory / "output" / "simulation1.out").write_text(
                "",
                encoding="utf-8",
            )
            (artifacts.output_directory / "simulation2.out").write_text(
                "",
                encoding="utf-8",
            )

            files = RunArtifactStore().list_output_files(artifacts)

            self.assertCountEqual(
                files,
                [
                    "input\\output\\simulation1.out",
                    "output\\simulation2.out",
                ],
            )


if __name__ == "__main__":
    unittest.main()
