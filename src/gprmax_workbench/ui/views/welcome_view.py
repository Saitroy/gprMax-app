from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .shared import PlaceholderView


class WelcomeView(PlaceholderView):
    def __init__(
        self,
        recent_projects: Sequence[Path] | None = None,
        parent=None,
    ) -> None:
        recent_text = "No recent projects yet."
        if recent_projects:
            recent_text = "\n".join(str(path) for path in recent_projects[:5])

        super().__init__(
            title="Welcome",
            subtitle=(
                "This workspace is the user-facing entrypoint for project creation, "
                "recent projects, onboarding, and guided workflows."
            ),
            sections=[
                (
                    "First-run goals",
                    "Stage 2 will add new/open/import project flows and a clearer "
                    "project dashboard for non-programmer users.",
                ),
                (
                    "Recent projects",
                    recent_text,
                ),
                (
                    "Product direction",
                    "The application should hide CLI friction while remaining "
                    "transparent about generated input, run status, and artifacts.",
                ),
            ],
            parent=parent,
        )
