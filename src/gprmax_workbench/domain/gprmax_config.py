from __future__ import annotations

from dataclasses import dataclass, field

from .execution_status import SimulationMode


@dataclass(slots=True)
class GprMaxRuntimeConfig:
    python_executable: str
    module_name: str = "gprMax"


@dataclass(slots=True)
class SimulationRunConfig:
    mode: SimulationMode = SimulationMode.NORMAL
    use_gpu: bool = False
    gpu_device_ids: list[int] = field(default_factory=list)
    benchmark: bool = False
    geometry_fixed: bool = False
    write_processed: bool = False
    num_model_runs: int = 1
    restart_from_model: int | None = None
    mpi_tasks: int | None = None
    mpi_no_spawn: bool = False
    extra_arguments: list[str] = field(default_factory=list)
