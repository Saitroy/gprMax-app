from __future__ import annotations

from pathlib import Path


class ResultsService:
    """Provides read-oriented access to run outputs and derived results."""

    def list_result_sets(self, project_root: Path) -> list[Path]:
        results_root = project_root / "results"
        if not results_root.exists():
            return []
        return sorted(path for path in results_root.iterdir() if path.is_dir())
