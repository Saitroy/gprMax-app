from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event

from ..domain.models import SimulationRequest


@dataclass(slots=True)
class SimulationJob:
    run_id: str
    request: SimulationRequest
    cancel_event: Event = field(default_factory=Event)

    def cancel(self) -> None:
        self.cancel_event.set()
