from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.execution_status import SimulationStatus
from gprmax_workbench.domain.gprmax_config import GprMaxRuntimeConfig, SimulationRunConfig
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
                runtime=GprMaxRuntimeConfig(
                    python_executable=sys.executable,
                    module_name="gprMax",
                ),
                runtime_label=f"{sys.executable} -m gprMax",
                exit_code=0,
                output_files=["output/model.out"],
                preflight_messages=["Bundled engine ready."],
                input_sha256="abc123",
            )

            repository = RunRepository()
            repository.save(record)
            loaded = repository.load(metadata_path)

            self.assertEqual(loaded.run_id, "run-001")
            self.assertEqual(loaded.status, SimulationStatus.COMPLETED)
            self.assertEqual(loaded.command[-1], "simulation.in")
            self.assertEqual(loaded.output_files, ["output/model.out"])
            self.assertIsNotNone(loaded.runtime)
            self.assertEqual(loaded.runtime.python_executable, sys.executable)
            self.assertEqual(loaded.runtime.module_name, "gprMax")
            self.assertEqual(loaded.runtime_label, f"{sys.executable} -m gprMax")
            self.assertEqual(loaded.preflight_messages, ["Bundled engine ready."])
            self.assertEqual(loaded.input_sha256, "abc123")

    def test_load_resolves_relative_paths_from_metadata_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            metadata_path = root / "examples" / "project" / "runs" / "run-001" / "metadata.json"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)

            payload = {
                "schema": {"name": "gprmax-workbench-run", "version": 1},
                "run_id": "run-001",
                "project_root": "..\\..",
                "project_name": "Portable Example",
                "status": "completed",
                "created_at": "2026-03-15T00:00:00+00:00",
                "started_at": "2026-03-15T00:00:00+00:00",
                "finished_at": "2026-03-15T00:00:01+00:00",
                "working_directory": ".",
                "input_file": "input\\simulation.in",
                "output_directory": "input\\output",
                "stdout_log_path": "logs\\stdout.log",
                "stderr_log_path": "logs\\stderr.log",
                "combined_log_path": "logs\\combined.log",
                "metadata_path": "metadata.json",
                "command": ["<bundled-python>", "-m", "gprMax", "input\\simulation.in"],
                "exit_code": 0,
                "error_summary": "",
                "output_files": [],
                "configuration": {"mode": "normal"},
            }
            metadata_path.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )

            loaded = RunRepository().load(metadata_path)

            self.assertEqual(loaded.project_root, metadata_path.parent.parent.parent.resolve())
            self.assertEqual(loaded.working_directory, metadata_path.parent.resolve())
            self.assertEqual(
                loaded.input_file,
                (metadata_path.parent / "input" / "simulation.in").resolve(),
            )
            self.assertEqual(
                loaded.output_directory,
                (metadata_path.parent / "input" / "output").resolve(),
            )


if __name__ == "__main__":
    unittest.main()
