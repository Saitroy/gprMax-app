from __future__ import annotations

from .shared import PlaceholderView


class SimulationView(PlaceholderView):
    def __init__(self, runtime_label: str, parent=None) -> None:
        super().__init__(
            title="Simulation Runner",
            subtitle=(
                "Runs, queues, logs, cancellation, and status reporting will live here. "
                "The current adapter target is shown below."
            ),
            sections=[
                (
                    "Runtime adapter",
                    runtime_label,
                ),
                (
                    "Execution model",
                    "The application will treat each run as a first-class artifact with "
                    "captured stdout, stderr, generated input snapshots, and metadata.",
                ),
                (
                    "Reliability goal",
                    "Simulation orchestration should remain stable even as gprMax "
                    "internals evolve, which is why subprocess integration is the baseline.",
                ),
            ],
            parent=parent,
        )
