from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ...domain.models import Project, SimulationRequest
from ...infrastructure.gprmax.adapter import GprMaxAdapter, GprMaxRunRequest


class SimulationService:
    """Builds run requests and delegates execution to the configured adapter."""

    def __init__(self, adapter: GprMaxAdapter) -> None:
        self._adapter = adapter

    def prepare_request(
        self,
        project: Project,
        input_file: Path,
        extra_arguments: Sequence[str] | None = None,
    ) -> SimulationRequest:
        return SimulationRequest(
            project_root=project.root,
            input_file=input_file,
            extra_arguments=list(extra_arguments or ()),
        )

    def build_command(self, request: SimulationRequest) -> list[str]:
        adapter_request = GprMaxRunRequest(
            working_directory=request.project_root,
            input_file=request.input_file,
            arguments=request.extra_arguments,
        )
        return self._adapter.build_command(adapter_request)

    def runtime_label(self) -> str:
        return self._adapter.describe_runtime()
