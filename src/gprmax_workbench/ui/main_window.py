from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .dialogs.new_project_dialog import NewProjectDialog
from .views.project_view import ProjectView
from .views.results_view import ResultsView
from .views.settings_view import SettingsView
from .views.simulation_view import SimulationView
from .views.welcome_view import WelcomeView

if TYPE_CHECKING:
    from ..app import ApplicationContext

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PageSpec:
    title: str
    description: str
    widget: QWidget


class MainWindow(QMainWindow):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._navigation = QListWidget()
        self._stack = QStackedWidget()

        self._welcome_view = WelcomeView()
        self._project_view = ProjectView()
        self._simulation_view = SimulationView(
            runtime_label=context.simulation_service.runtime_label()
        )
        self._results_view = ResultsView()
        self._settings_view = SettingsView()
        self._pages = self._build_pages()

        self._save_project_action = QAction("Save Project", self)

        self.setWindowTitle("GPRMax Workbench")
        self.resize(1360, 860)

        self._connect_signals()
        self._create_actions()
        self._build_ui()
        self.refresh_views()

    def _build_pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                title="Welcome",
                description="Project manager and onboarding entrypoint.",
                widget=self._welcome_view,
            ),
            PageSpec(
                title="Model Editor",
                description="Essential project settings and core model metadata.",
                widget=self._project_view,
            ),
            PageSpec(
                title="Simulation",
                description="Run preparation, execution, and logs.",
                widget=self._simulation_view,
            ),
            PageSpec(
                title="Results",
                description="Run outputs and viewer entrypoints.",
                widget=self._results_view,
            ),
            PageSpec(
                title="Settings",
                description="Application and runtime settings.",
                widget=self._settings_view,
            ),
        ]

    def _connect_signals(self) -> None:
        self._welcome_view.new_project_requested.connect(self._on_new_project)
        self._welcome_view.open_project_requested.connect(self._on_open_project)
        self._welcome_view.recent_project_requested.connect(self._on_open_recent_project)
        self._project_view.save_requested.connect(self._on_save_project)
        self._settings_view.save_requested.connect(self._on_save_settings)

    def _create_actions(self) -> None:
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self._on_new_project)

        open_project_action = QAction("Open Project", self)
        open_project_action.triggered.connect(self._on_open_project)

        self._save_project_action.triggered.connect(self._on_save_project)

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)

        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(new_project_action)
        file_menu.addAction(open_project_action)
        file_menu.addAction(self._save_project_action)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(about_action)

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        sidebar = self._build_sidebar()
        content = self._build_content_stack()

        layout.addWidget(sidebar, 0)
        layout.addWidget(content, 1)

        self.setCentralWidget(central)
        self.statusBar().showMessage(
            "Stage 2 foundation ready for project and settings flows."
        )

    def refresh_views(self) -> None:
        workspace = self._context.workspace_service
        settings_service = self._context.settings_service

        project = workspace.state.current_project
        validation = workspace.state.current_project_validation
        project_file = workspace.current_project_file()

        self._welcome_view.set_current_project(project)
        self._welcome_view.set_recent_projects(workspace.state.recent_projects)
        self._project_view.set_project(
            project=project,
            validation=validation,
            is_dirty=workspace.state.current_project_dirty,
            project_file=str(project_file) if project_file else None,
        )
        self._settings_view.set_settings(
            settings=settings_service.settings,
            summary=settings_service.runtime_summary(),
        )
        self._simulation_view.set_runtime_label(
            self._context.simulation_service.runtime_label()
        )
        self._save_project_action.setEnabled(project is not None)
        self._update_window_title()

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("Sidebar")
        frame.setMinimumWidth(260)
        frame.setMaximumWidth(300)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("GPRMax\nWorkbench")
        title.setObjectName("AppTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        subtitle = QLabel(
            "Desktop orchestration layer for guided modelling and simulation runs."
        )
        subtitle.setObjectName("AppSubtitle")
        subtitle.setWordWrap(True)

        self._navigation.setObjectName("Navigation")
        self._navigation.setSpacing(4)
        self._navigation.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        for page in self._pages:
            item = QListWidgetItem(page.title)
            item.setToolTip(page.description)
            self._navigation.addItem(item)

        self._navigation.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._navigation.currentRowChanged.connect(self._update_status)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self._navigation)

        return frame

    def _build_content_stack(self) -> QWidget:
        for page in self._pages:
            self._stack.addWidget(page.widget)
        self._navigation.setCurrentRow(0)
        return self._stack

    def _update_status(self, index: int) -> None:
        if index < 0 or index >= len(self._pages):
            return
        self.statusBar().showMessage(self._pages[index].description)

    def _update_window_title(self) -> None:
        current_project = self._context.workspace_service.state.current_project
        if current_project is None:
            self.setWindowTitle("GPRMax Workbench")
            return

        dirty_marker = "*" if self._context.workspace_service.state.current_project_dirty else ""
        self.setWindowTitle(
            f"GPRMax Workbench - {current_project.metadata.name}{dirty_marker}"
        )

    def _on_new_project(self) -> None:
        dialog = NewProjectDialog(self)
        if dialog.exec() == 0:
            return

        try:
            project = self._context.workspace_service.create_project(
                root=dialog.project_root(),
                name=dialog.project_name(),
            )
        except Exception as exc:
            LOGGER.exception("Failed to create project")
            QMessageBox.critical(self, "New Project", str(exc))
            return

        self.refresh_views()
        self._navigation.setCurrentRow(1)
        self.statusBar().showMessage(
            f"Created project '{project.metadata.name}' at {project.root}",
            6000,
        )

    def _on_open_project(self) -> None:
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Open Project Directory",
            str(Path.home()),
        )
        if not project_dir:
            return

        self._open_project_at(Path(project_dir))

    def _on_open_recent_project(self, path: str) -> None:
        self._open_project_at(Path(path))

    def _open_project_at(self, path: Path) -> None:
        try:
            project = self._context.workspace_service.open_project(path)
        except Exception as exc:
            LOGGER.exception("Failed to open project at %s", path)
            QMessageBox.critical(self, "Open Project", str(exc))
            return

        self.refresh_views()
        self._navigation.setCurrentRow(1)
        self.statusBar().showMessage(
            f"Opened project '{project.metadata.name}'",
            6000,
        )

    def _on_save_project(self) -> None:
        if self._context.workspace_service.state.current_project is None:
            QMessageBox.information(
                self,
                "Save Project",
                "Create or open a project before saving.",
            )
            return

        draft = self._project_view.collect_draft()
        validation = self._context.workspace_service.save_draft(draft)
        self.refresh_views()

        if not validation.is_valid:
            QMessageBox.warning(
                self,
                "Save Project",
                "\n".join(
                    f"{issue.path}: {issue.message}" for issue in validation.errors
                ),
            )
            return

        warning_text = ""
        if validation.warnings:
            warning_text = (
                " Saved with warnings: "
                + "; ".join(issue.message for issue in validation.warnings)
            )

        self.statusBar().showMessage(
            f"Project saved successfully.{warning_text}",
            8000,
        )

    def _on_save_settings(self) -> None:
        settings = self._context.settings_service.update_preferences(
            advanced_mode=self._settings_view.advanced_mode_enabled(),
            gprmax_python_executable=self._settings_view.runtime_executable(),
        )
        self._context.gprmax_adapter.configure_runtime(
            settings.gprmax_python_executable
        )
        self.refresh_views()
        self.statusBar().showMessage("Settings saved.", 5000)

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About GPRMax Workbench",
            "Stage 2 foundation: project model, settings, persistence, validation, and UI flows.",
        )
