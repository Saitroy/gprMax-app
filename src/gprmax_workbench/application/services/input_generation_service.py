from __future__ import annotations

from pathlib import Path

from ...domain.gprmax_config import SimulationRunConfig
from ...domain.models import Project
from ...domain.validation import ValidationResult, validate_project_for_execution
from ...infrastructure.gprmax.input_generator import (
    GeneratedInput,
    GprMaxInputGenerator,
)
from ...infrastructure.persistence.artifact_store import RunArtifactStore


class InputGenerationService:
    """Builds preview/exported gprMax input from the current project model."""

    def __init__(
        self,
        generator: GprMaxInputGenerator,
        artifact_store: RunArtifactStore,
    ) -> None:
        self._generator = generator
        self._artifact_store = artifact_store

    def validate_before_run(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> ValidationResult:
        return validate_project_for_execution(project, configuration)

    def build_input_preview(
        self,
        project: Project,
        configuration: SimulationRunConfig,
    ) -> GeneratedInput:
        return self._generator.generate(
            project=project,
            configuration=configuration,
            output_dir="output",
        )

    def export_preview(
        self,
        project: Project,
        configuration: SimulationRunConfig,
        destination: Path | None = None,
    ) -> Path:
        generated = self.build_input_preview(project, configuration)
        if destination is None:
            destination = project.root / "generated" / "preview.in"
        return self._artifact_store.export_input(destination, generated.text)
