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


def project_scan_trace_count(project: Project | None) -> int | None:
    if project is None:
        return None
    return project.model.scan_trace_count
