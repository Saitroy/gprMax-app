"""Domain layer."""

from .execution_status import SimulationMode, SimulationStatus
from .gprmax_config import GprMaxRuntimeConfig, SimulationRunConfig
from .models import Project, ProjectModel, Vector3, default_project
from .simulation import PreparedSimulationRun, RunArtifacts, SimulationLogSnapshot, SimulationRunRecord

__all__ = [
    "GprMaxRuntimeConfig",
    "PreparedSimulationRun",
    "Project",
    "ProjectModel",
    "RunArtifacts",
    "SimulationLogSnapshot",
    "SimulationMode",
    "SimulationRunConfig",
    "SimulationRunRecord",
    "SimulationStatus",
    "Vector3",
    "default_project",
]
