from __future__ import annotations

from .shared import PlaceholderView


class ProjectView(PlaceholderView):
    def __init__(self, parent=None) -> None:
        super().__init__(
            title="Model Editor",
            subtitle=(
                "This area will host guided editors for materials, geometry, sources, "
                "receivers, grid settings, and advanced overrides."
            ),
            sections=[
                (
                    "MVP scope",
                    "The first editor pass should prioritize validated forms and "
                    "sensible defaults over a visually complex canvas.",
                ),
                (
                    "Transparency",
                    "Every GUI edit must be traceable to generated gprMax input so "
                    "users can understand and trust the translation layer.",
                ),
                (
                    "Advanced mode",
                    "Expert users will be able to inspect and override raw input "
                    "without bypassing the project model entirely.",
                ),
            ],
            parent=parent,
        )
