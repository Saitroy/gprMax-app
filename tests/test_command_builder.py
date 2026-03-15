from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.domain.execution_status import SimulationMode
from gprmax_workbench.domain.gprmax_config import GprMaxRuntimeConfig, SimulationRunConfig
from gprmax_workbench.infrastructure.gprmax.command_builder import (
    GprMaxCommandBuilder,
    GprMaxCommandRequest,
)


class CommandBuilderTests(unittest.TestCase):
    def test_builds_expected_flags(self) -> None:
        builder = GprMaxCommandBuilder()
        runtime = GprMaxRuntimeConfig(python_executable="python")
        request = GprMaxCommandRequest(
            working_directory=Path("C:/work"),
            input_file=Path("C:/work/runs/001/input/simulation.in"),
            configuration=SimulationRunConfig(
                mode=SimulationMode.GEOMETRY_ONLY,
                use_gpu=True,
                gpu_device_ids=[0, 1],
                geometry_fixed=True,
                write_processed=True,
                num_model_runs=3,
                restart_from_model=2,
                mpi_tasks=4,
                mpi_no_spawn=True,
                extra_arguments=["--dry-run"],
            ),
        )

        command = builder.build(runtime, request)

        self.assertEqual(command[:4], ["python", "-m", "gprMax", str(request.input_file)])
        self.assertIn("--geometry-only", command)
        self.assertIn("-gpu", command)
        self.assertIn("0", command)
        self.assertIn("1", command)
        self.assertIn("--geometry-fixed", command)
        self.assertIn("--write-processed", command)
        self.assertIn("-n", command)
        self.assertIn("-restart", command)
        self.assertIn("-mpi", command)
        self.assertIn("--mpi-no-spawn", command)
        self.assertEqual(command[-1], "--dry-run")


if __name__ == "__main__":
    unittest.main()
