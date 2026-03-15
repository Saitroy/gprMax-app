from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ...domain.gprmax_config import SimulationRunConfig
from ...domain.models import Project
from ...infrastructure.gprmax.input_generator import InputGenerationError
from .input_generation_service import InputGenerationService
from .validation_service import ValidationService


@dataclass(slots=True)
class InputPreviewResult:
    text: str
    messages: list[str] = field(default_factory=list)
    generated: bool = False


class InputPreviewService:
    """Builds editor-side gprMax input previews without invoking the runner."""

    def __init__(
        self,
        input_generation_service: InputGenerationService,
        validation_service: ValidationService,
    ) -> None:
        self._input_generation_service = input_generation_service
        self._validation_service = validation_service

    def generate_preview(
        self,
        project: Project,
        configuration: SimulationRunConfig | None = None,
    ) -> InputPreviewResult:
        run_configuration = configuration or SimulationRunConfig()
        validation = self._validation_service.validate_model(project)
        messages = [
            f"{issue.severity.value}: {issue.path} - {issue.message}"
            for issue in validation.issues
        ]

        try:
            generated = self._input_generation_service.build_input_preview(
                project=project,
                configuration=run_configuration,
            )
        except InputGenerationError as exc:
            messages.append(f"error: preview - {exc}")
            return InputPreviewResult(text="", messages=messages, generated=False)

        messages.extend(generated.warnings)
        return InputPreviewResult(
            text=generated.text,
            messages=messages,
            generated=True,
        )

    def export_preview(
        self,
        project: Project,
        destination: Path,
        configuration: SimulationRunConfig | None = None,
    ) -> Path:
        run_configuration = configuration or SimulationRunConfig()
        return self._input_generation_service.export_preview(
            project=project,
            configuration=run_configuration,
            destination=destination,
        )
