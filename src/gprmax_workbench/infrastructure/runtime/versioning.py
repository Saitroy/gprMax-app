from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


class VersioningService:
    """Loads application and bundled-engine version information."""

    def app_version(self) -> str:
        try:
            return version("gprmax-workbench")
        except PackageNotFoundError:
            return "0.2.1-dev"

    def load_engine_manifest(self, manifest_path: Path) -> dict[str, str]:
        if not manifest_path.exists():
            return {}
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {
            key: str(value)
            for key, value in payload.items()
            if value is not None and isinstance(value, (str, int, float, bool))
        }
