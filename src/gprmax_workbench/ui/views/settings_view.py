from __future__ import annotations

from typing import Mapping

from .shared import PlaceholderView


class SettingsView(PlaceholderView):
    def __init__(self, summary: Mapping[str, str], parent=None) -> None:
        body = "\n".join(f"{key}: {value}" for key, value in summary.items())

        super().__init__(
            title="Settings",
            subtitle=(
                "Application settings, runtime configuration, and future installer-level "
                "environment diagnostics will be centralized here."
            ),
            sections=[
                (
                    "Current runtime summary",
                    body,
                ),
                (
                    "Planned settings",
                    "Recent projects, gprMax runtime discovery, advanced mode, logging, "
                    "and default run behavior belong in this workspace.",
                ),
                (
                    "Packaging implication",
                    "This screen will eventually help distinguish bundled runtime "
                    "settings from user-managed external runtimes.",
                ),
            ],
            parent=parent,
        )
