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
from gprmax_workbench.infrastructure.persistence.run_repository import RunRepository


class RunRepositoryTests(unittest.TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            metadata_path = root / "runs" / "run-001" / "metadata.json"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)

            record = SimulationRunRecord(
                run_id="run-001",
                project_root=root,
                project_name="Run Demo",
                status=SimulationStatus.COMPLETED,
                created_at=datetime(2026, 3, 15, tzinfo=UTC),
                started_at=datetime(2026, 3, 15, tzinfo=UTC),
                finished_at=datetime(2026, 3, 15, tzinfo=UTC),
                working_directory=metadata_path.parent,
                input_file=metadata_path.parent / "input" / "simulation.in",
                output_directory=metadata_path.parent / "output",
                stdout_log_path=metadata_path.parent / "logs" / "stdout.log",
                stderr_log_path=metadata_path.parent / "logs" / "stderr.log",
                combined_log_path=metadata_path.parent / "logs" / "combined.log",
                metadata_path=metadata_path,
                configuration=SimulationRunConfig(),
                command=["python", "-m", "gprMax", "simulation.in"],
                exit_code=0,
                output_files=["output/model.out"],
            )

            repository = RunRepository()
            repository.save(record)
            loaded = repository.load(metadata_path)

            self.assertEqual(loaded.run_id, "run-001")
            self.assertEqual(loaded.status, SimulationStatus.COMPLETED)
            self.assertEqual(loaded.command[-1], "simulation.in")
            self.assertEqual(loaded.output_files, ["output/model.out"])


if __name__ == "__main__":
    unittest.main()
