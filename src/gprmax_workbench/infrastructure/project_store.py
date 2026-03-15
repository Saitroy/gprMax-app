from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..domain.models import Project, ProjectMetadata

PROJECT_FILENAME = "project.gprwb.json"


class JsonProjectStore:
    """Stores project metadata and editor state in a JSON manifest."""

    def project_file(self, root: Path) -> Path:
        return root.expanduser().resolve() / PROJECT_FILENAME

    def save(self, project: Project) -> Path:
        project.root.mkdir(parents=True, exist_ok=True)
        project_file = self.project_file(project.root)
        payload = {
            "metadata": {
                "name": project.metadata.name,
                "description": project.metadata.description,
                "created_at": project.metadata.created_at.isoformat(),
                "updated_at": project.metadata.updated_at.isoformat(),
            },
            "model": project.model,
            "advanced_input_overrides": project.advanced_input_overrides,
        }
        project_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return project_file

    def load(self, root: Path) -> Project:
        project_file = self.project_file(root)
        payload = json.loads(project_file.read_text(encoding="utf-8"))
        metadata = payload["metadata"]

        return Project(
            root=root.expanduser().resolve(),
            metadata=ProjectMetadata(
                name=metadata["name"],
                description=metadata.get("description", ""),
                created_at=_parse_datetime(metadata["created_at"]),
                updated_at=_parse_datetime(metadata["updated_at"]),
            ),
            model=_as_dict(payload.get("model")),
            advanced_input_overrides=_as_dict(
                payload.get("advanced_input_overrides")
            ),
        )


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
