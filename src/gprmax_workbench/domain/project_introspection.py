from __future__ import annotations

from .models import Project


def project_uses_scan_steps(project: Project | None) -> bool:
    if project is None:
        return False

    for line in project.advanced_input_overrides:
        normalized = line.strip().lower()
        if normalized.startswith("#src_steps:") or normalized.startswith("#rx_steps:"):
            return True
    return False
