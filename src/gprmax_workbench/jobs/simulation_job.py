from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event

from ..domain.gprmax_config import SimulationRunConfig


@dataclass(slots=True)
class SimulationJob:
    run_id: str
    project_root: Path
    configuration: SimulationRunConfig
    cancel_event: Event = field(default_factory=Event)

    def cancel(self) -> None:
        self.cancel_event.set()
