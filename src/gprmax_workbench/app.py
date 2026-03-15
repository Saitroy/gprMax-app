from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .application.services.project_service import ProjectService
from .application.services.results_service import ResultsService
from .application.services.settings_service import SettingsService
from .application.services.simulation_service import SimulationService
from .application.state import AppState
from .infrastructure.gprmax.adapter import SubprocessGprMaxAdapter
from .infrastructure.logging import setup_logging
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
    simulation_service: SimulationService
    results_service: ResultsService
    state: AppState


def build_context() -> ApplicationContext:
    settings_manager = SettingsManager(app_name="gprmax_workbench")
    setup_logging(settings_manager.logs_dir)

    settings_service = SettingsService(settings_manager)
    project_store = JsonProjectStore()
    gprmax_adapter = SubprocessGprMaxAdapter(
        python_executable=settings_service.settings.gprmax_python_executable
    )
    project_service = ProjectService(
        project_store=project_store,
        settings_service=settings_service,
    )
    simulation_service = SimulationService(adapter=gprmax_adapter)
    results_service = ResultsService()
    state = AppState(recent_projects=settings_service.recent_projects())

    LOGGER.debug("Application context created")

    return ApplicationContext(
        settings_manager=settings_manager,
        settings_service=settings_service,
        project_store=project_store,
        project_service=project_service,
        gprmax_adapter=gprmax_adapter,
        simulation_service=simulation_service,
        results_service=results_service,
        state=state,
    )


def create_application() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    apply_theme(app)
    return app


def run(initial_project: str | None = None) -> int:
    context = build_context()
    app = create_application()
    main_window = MainWindow(context=context)

    if initial_project:
        context.state.startup_project = Path(initial_project).expanduser().resolve()
        LOGGER.info("Startup project requested: %s", context.state.startup_project)

    main_window.show()
    return app.exec()
