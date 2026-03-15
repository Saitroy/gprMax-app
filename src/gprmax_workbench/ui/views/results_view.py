from __future__ import annotations

from .shared import PlaceholderView


class ResultsView(PlaceholderView):
    def __init__(self, parent=None) -> None:
        super().__init__(
            title="Results Viewer",
            subtitle=(
                "This workspace will expose result discovery, run-centric navigation, "
                "and the first extensible viewers for common outputs."
            ),
            sections=[
                (
                    "Near-term scope",
                    "Stage 5 should at least let users browse runs, inspect artifacts, "
                    "and open result folders directly from the app.",
                ),
                (
                    "Viewer architecture",
                    "The results layer should allow later analyzers and custom viewers "
                    "without coupling them to the simulation runner implementation.",
                ),
                (
                    "User promise",
                    "Users should always know where their outputs are stored and what "
                    "produced them.",
                ),
            ],
            parent=parent,
        )
