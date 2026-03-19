from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .application.services.input_preview_service import InputPreviewService
from .application.services.input_generation_service import InputGenerationService
from .application.services.bscan_service import BscanService
from .application.services.diagnostics_service import DiagnosticsService
from .application.services.engine_resolution_service import EngineResolutionService
from .application.services.localization_service import LocalizationService
from .application.services.model_editor_service import ModelEditorService
from .application.services.project_service import ProjectService
from .application.services.results_service import ResultsService
from .application.services.runtime_service import RuntimeService
from .application.services.run_service import RunService
from .application.services.settings_service import SettingsService
from .application.services.simulation_service import SimulationService
from .application.services.trace_service import TraceService
from .application.services.validation_service import ValidationService
from .application.services.workspace_service import WorkspaceService
from .application.state import AppState
from .infrastructure.gprmax.adapter import SubprocessGprMaxAdapter
from .infrastructure.gprmax.input_generator import GprMaxInputGenerator
from .infrastructure.gprmax.runner import GprMaxSubprocessRunner
from .infrastructure.logging import setup_logging
from .infrastructure.persistence.artifact_store import RunArtifactStore
from .infrastructure.persistence.run_repository import RunRepository
from .infrastructure.project_store import JsonProjectStore
from .infrastructure.results.artifact_locator import ResultArtifactLocator
from .infrastructure.results.bscan_builder import BscanBuilder
from .infrastructure.results.hdf5_reader import Hdf5ResultsReader
from .infrastructure.results.result_repository import ResultRepository
from .infrastructure.runtime.bundled_runtime import BundledRuntimeProvider
from .infrastructure.runtime.diagnostics import RuntimeDiagnostics
from .infrastructure.runtime.engine_locator import EngineLocator
from .infrastructure.runtime.external_runtime import ExternalRuntimeProvider
from .infrastructure.runtime.path_manager import PathManager
from .infrastructure.runtime.versioning import VersioningService
from .infrastructure.settings import SettingsManager
from .ui.main_window import MainWindow
from .ui.theme import apply_theme

APP_NAME = "GPRMax Workbench"
ORGANIZATION_NAME = "GPRMax Workbench"
LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ApplicationContext:
    settings_manager: SettingsManager
    settings_service: SettingsService
    localization_service: LocalizationService
    runtime_service: RuntimeService
    project_store: JsonProjectStore
    project_service: ProjectService
    gprmax_adapter: SubprocessGprMaxAdapter
    model_editor_service: ModelEditorService
    validation_service: ValidationService
    input_generation_service: InputGenerationService
    input_preview_service: InputPreviewService
    simulation_service: SimulationService
    run_service: RunService
    results_service: ResultsService
    trace_service: TraceService
    bscan_service: BscanService
    state: AppState
    workspace_service: WorkspaceService


def build_context() -> ApplicationContext:
    settings_manager = SettingsManager(app_name="gprmax_workbench")
    setup_logging(settings_manager.logs_dir)
    path_manager = PathManager(settings_manager=settings_manager)
    path_manager.ensure_user_runtime_directories()

    settings_service = SettingsService(settings_manager)
    localization_service = LocalizationService(settings_service.settings.language)
    gprmax_adapter = SubprocessGprMaxAdapter()
    runtime_service = RuntimeService(
        settings_service=settings_service,
        engine_resolution_service=EngineResolutionService(
            EngineLocator(
                bundled_provider=BundledRuntimeProvider(path_manager),
                external_provider=ExternalRuntimeProvider(),
            )
        ),
        diagnostics_service=DiagnosticsService(
            RuntimeDiagnostics(
                path_manager=path_manager,
                versioning=VersioningService(),
            )
        ),
        adapter=gprmax_adapter,
    )
    runtime_service.refresh()
    project_store = JsonProjectStore()
    artifact_store = RunArtifactStore()
    run_repository = RunRepository()
    results_repository = ResultRepository(
        run_repository=run_repository,
        artifact_locator=ResultArtifactLocator(),
        reader=Hdf5ResultsReader(),
    )
    project_service = ProjectService(
        project_store=project_store,
        settings_service=settings_service,
    )
    state = AppState(recent_projects=settings_service.recent_projects())
    validation_service = ValidationService(state)
    model_editor_service = ModelEditorService(state)
    workspace_service = WorkspaceService(
        project_service=project_service,
        settings_service=settings_service,
        state=state,
    )
    input_generation_service = InputGenerationService(
        generator=GprMaxInputGenerator(),
        artifact_store=artifact_store,
    )
    input_preview_service = InputPreviewService(
        input_generation_service=input_generation_service,
        validation_service=validation_service,
    )
    simulation_service = SimulationService(
        adapter=gprmax_adapter,
        input_generation_service=input_generation_service,
        artifact_store=artifact_store,
        run_repository=run_repository,
        runner=GprMaxSubprocessRunner(),
        state=state,
        runtime_info_provider=runtime_service.runtime_info,
    )
    run_service = RunService(run_repository)
    results_service = ResultsService(
        result_repository=results_repository,
        state=state,
    )
    trace_service = TraceService(results_repository)
    bscan_service = BscanService(BscanBuilder(Hdf5ResultsReader()))

    LOGGER.debug("Application context created")

    return ApplicationContext(
        settings_manager=settings_manager,
        settings_service=settings_service,
        localization_service=localization_service,
        runtime_service=runtime_service,
        project_store=project_store,
        project_service=project_service,
        gprmax_adapter=gprmax_adapter,
        model_editor_service=model_editor_service,
        validation_service=validation_service,
        input_generation_service=input_generation_service,
        input_preview_service=input_preview_service,
        simulation_service=simulation_service,
        run_service=run_service,
        results_service=results_service,
        trace_service=trace_service,
        bscan_service=bscan_service,
        state=state,
        workspace_service=workspace_service,
    )


def create_application() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    apply_theme(app)
    return app


def run(initial_project: str | None = None) -> int:
    context = build_context()

    if initial_project:
        context.state.startup_project = Path(initial_project).expanduser().resolve()
        LOGGER.info("Startup project requested: %s", context.state.startup_project)
        try:
            context.workspace_service.open_project(context.state.startup_project)
        except Exception:
            LOGGER.exception(
                "Failed to open startup project at %s",
                context.state.startup_project,
            )

    app = create_application()
    main_window = MainWindow(context=context)

    main_window.show()
    return app.exec()
