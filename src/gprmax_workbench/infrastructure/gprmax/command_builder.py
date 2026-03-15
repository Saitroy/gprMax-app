from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...domain.gprmax_config import GprMaxRuntimeConfig, SimulationRunConfig
from ...domain.execution_status import SimulationMode


@dataclass(slots=True)
class GprMaxCommandRequest:
    working_directory: Path
    input_file: Path
    configuration: SimulationRunConfig


class GprMaxCommandBuilder:
    """Builds stable gprMax CLI commands from typed run configuration."""

    def build(
        self,
        runtime: GprMaxRuntimeConfig,
        request: GprMaxCommandRequest,
    ) -> list[str]:
        command = [
            runtime.python_executable,
            "-m",
            runtime.module_name,
            str(request.input_file),
        ]

        configuration = request.configuration

        if configuration.mode == SimulationMode.GEOMETRY_ONLY:
            command.append("--geometry-only")
        if configuration.use_gpu:
            command.append("-gpu")
            if configuration.gpu_device_ids:
                command.extend(str(item) for item in configuration.gpu_device_ids)
        if configuration.geometry_fixed:
            command.append("--geometry-fixed")
        if configuration.write_processed:
            command.append("--write-processed")
        if configuration.benchmark:
            command.append("-benchmark")
        if configuration.num_model_runs > 1:
            command.extend(["-n", str(configuration.num_model_runs)])
        if configuration.restart_from_model is not None:
            command.extend(["-restart", str(configuration.restart_from_model)])
        if configuration.mpi_tasks is not None and configuration.mpi_tasks > 0:
            command.extend(["-mpi", str(configuration.mpi_tasks)])
        if configuration.mpi_no_spawn:
            command.append("--mpi-no-spawn")
        command.extend(configuration.extra_arguments)

        return command
