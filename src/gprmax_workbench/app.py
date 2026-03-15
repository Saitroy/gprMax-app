from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .application.services.input_generation_service import InputGenerationService
from .application.services.project_service import ProjectService
from .application.services.results_service import ResultsService
from .application.services.run_service import RunService
from .application.services.settings_service import SettingsService
from .application.services.simulation_service import SimulationService
from .application.services.workspace_service import WorkspaceService
from .application.state import AppState
from .infrastructure.gprmax.adapter import SubprocessGprMaxAdapter
from .infrastructure.gprmax.input_generator import GprMaxInputGenerator
from .infrastructure.gprmax.runner import GprMaxSubprocessRunner
from .infrastructure.logging import setup_logging
from .infrastructure.persistence.artifact_store import RunArtifactStore
from .infrastructure.persistence.run_repository import RunRepository
from .infrastructure.project_store import JsonProjectStore
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
    project_store: JsonProjectStore
    project_service: ProjectService
    gprmax_adapter: SubprocessGprMaxAdapter
    input_generation_service: InputGenerationService
    simulation_service: SimulationService
    run_service: RunService
    results_service: ResultsService
    state: AppState
    workspace_service: WorkspaceService


def build_context() -> ApplicationContext:
    settings_manager = SettingsManager(app_name="gprmax_workbench")
    setup_logging(settings_manager.logs_dir)

    settings_service = SettingsService(settings_manager)
    project_store = JsonProjectStore()
    artifact_store = RunArtifactStore()
    run_repository = RunRepository()
    gprmax_adapter = SubprocessGprMaxAdapter(
        python_executable=settings_service.settings.gprmax_python_executable
    )
    project_service = ProjectService(
        project_store=project_store,
        settings_service=settings_service,
    )
    state = AppState(recent_projects=settings_service.recent_projects())
    workspace_service = WorkspaceService(
        project_service=project_service,
        settings_service=settings_service,
        state=state,
    )
    input_generation_service = InputGenerationService(
        generator=GprMaxInputGenerator(),
        artifact_store=artifact_store,
    )
    simulation_service = SimulationService(
        adapter=gprmax_adapter,
        input_generation_service=input_generation_service,
        artifact_store=artifact_store,
        run_repository=run_repository,
        runner=GprMaxSubprocessRunner(),
        state=state,
    )
    run_service = RunService(run_repository)
    results_service = ResultsService()

    LOGGER.debug("Application context created")

    return ApplicationContext(
        settings_manager=settings_manager,
        settings_service=settings_service,
        project_store=project_store,
        project_service=project_service,
        gprmax_adapter=gprmax_adapter,
        input_generation_service=input_generation_service,
        simulation_service=simulation_service,
        run_service=run_service,
        results_service=results_service,
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
