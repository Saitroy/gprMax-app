from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ResultsViewerState:
    selected_run_id: str | None = None
    selected_output_file: str | None = None
    selected_receiver_id: str | None = None
    selected_component: str | None = None
    selected_ascan_components: list[str] = field(default_factory=list)
