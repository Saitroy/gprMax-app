from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices
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

from ..application.services.project_service import ProjectValidationError
from ..application.services.simulation_service import (
    SimulationPreparationError,
)
from .dialogs.new_project_dialog import NewProjectDialog
from .views.project_view import ProjectView
from .views.results_view import ResultsView
from .views.settings_view import SettingsView
from .views.simulation_view import SimulationView
from .views.welcome_view import WelcomeView

if TYPE_CHECKING:
    from ..app import ApplicationContext
    from ..domain.simulation import SimulationRunRecord

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
        self._simulation_refresh_timer = QTimer(self)
        self._simulation_refresh_timer.setInterval(400)
        self._simulation_refresh_timer.timeout.connect(self._refresh_simulation_runtime_state)

        self._welcome_view = WelcomeView()
        self._project_view = ProjectView(
            model_editor_service=context.model_editor_service,
            validation_service=context.validation_service,
            input_preview_service=context.input_preview_service,
        )
        self._simulation_view = SimulationView(
            runtime_label=context.simulation_service.runtime_label()
        )
        self._results_view = ResultsView()
        self._settings_view = SettingsView()
        self._pages = self._build_pages()

        self._save_project_action = QAction("Save Project", self)

        self.setWindowTitle("GPRMax Workbench")
        self.resize(1440, 920)

        self._connect_signals()
        self._create_actions()
        self._build_ui()
        self.refresh_views()
        self._simulation_refresh_timer.start()

    def _build_pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                title="Welcome",
                description="Project manager and onboarding entrypoint.",
                widget=self._welcome_view,
            ),
            PageSpec(
                title="Model Editor",
                description="Form-based MVP editor for model setup, materials, entities, and input preview.",
                widget=self._project_view,
            ),
            PageSpec(
                title="Simulation",
                description="Input generation, execution, logs, and run history.",
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
        self._project_view.editor_changed.connect(self._on_project_editor_changed)
        self._settings_view.save_requested.connect(self._on_save_settings)
        self._simulation_view.preview_requested.connect(self._on_preview_input)
        self._simulation_view.export_requested.connect(self._on_export_input)
        self._simulation_view.start_requested.connect(self._on_start_run)
        self._simulation_view.cancel_requested.connect(self._on_cancel_run)
        self._simulation_view.open_run_directory_requested.connect(
            self._on_open_run_directory
        )
        self._simulation_view.open_output_directory_requested.connect(
            self._on_open_output_directory
        )

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
            "Stage 4 foundation ready for guided model editing and Stage 3 execution flow."
        )

    def refresh_views(self) -> None:
        workspace = self._context.workspace_service
        settings_service = self._context.settings_service

        project = workspace.state.current_project
        validation = workspace.state.current_project_validation
        project_file = workspace.current_project_file()

        if project is not None:
            self._context.simulation_service.get_run_history(project.root)
            self._simulation_view.set_project_state(
                project_name=project.metadata.name,
                is_dirty=workspace.state.current_project_dirty,
            )
        else:
            self._simulation_view.set_project_state(project_name=None, is_dirty=False)
            workspace.state.run_history = []

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
        self._refresh_simulation_runtime_state()

    def _refresh_shell_state(self) -> None:
        workspace = self._context.workspace_service
        project = workspace.state.current_project
        self._welcome_view.set_current_project(project)
        self._simulation_view.set_project_state(
            project_name=project.metadata.name if project else None,
            is_dirty=workspace.state.current_project_dirty,
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
        active_run = self._context.workspace_service.state.active_run
        if current_project is None:
            self.setWindowTitle("GPRMax Workbench")
            return

        dirty_marker = "*" if self._context.workspace_service.state.current_project_dirty else ""
        run_suffix = ""
        if active_run is not None and active_run.status.value in {"preparing", "running"}:
            run_suffix = f" [{active_run.status.value}: {active_run.run_id}]"
        self.setWindowTitle(
            f"GPRMax Workbench - {current_project.metadata.name}{dirty_marker}{run_suffix}"
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

        try:
            validation = self._context.workspace_service.save_current_project()
        except ProjectValidationError as exc:
            QMessageBox.warning(
                self,
                "Save Project",
                "\n".join(
                    f"{issue.path}: {issue.message}"
                    for issue in exc.validation.errors
                ),
            )
            return

        self.refresh_views()

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

    def _on_project_editor_changed(self) -> None:
        self._refresh_shell_state()

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

    def _on_preview_input(self) -> None:
        project = self._current_project_or_warn()
        if project is None:
            return

        configuration = self._simulation_view.current_configuration()
        validation = self._context.simulation_service.validate_before_run(
            project,
            configuration,
        )
        messages = [
            f"{issue.severity.value}: {issue.path} - {issue.message}"
            for issue in validation.issues
        ]

        try:
            prepared = self._context.simulation_service.rebuild_input_preview(
                project,
                configuration,
            )
        except Exception as exc:
            LOGGER.exception("Failed to build input preview")
            QMessageBox.warning(self, "Input Preview", str(exc))
            return

        self._simulation_view.set_input_preview(prepared.preview_text)
        self._simulation_view.set_validation_messages(
            messages + prepared.validation_messages
        )
        self.statusBar().showMessage("Input preview rebuilt.", 5000)

    def _on_export_input(self) -> None:
        project = self._current_project_or_warn()
        if project is None:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export gprMax Input",
            str(project.root / "generated" / "exported.in"),
            "gprMax input (*.in);;All files (*)",
        )
        if not filename:
            return

        try:
            destination = self._context.simulation_service.export_input(
                project,
                self._simulation_view.current_configuration(),
                Path(filename),
            )
        except Exception as exc:
            LOGGER.exception("Failed to export input")
            QMessageBox.warning(self, "Export Input", str(exc))
            return

        self.statusBar().showMessage(f"Exported input to {destination}", 6000)

    def _on_start_run(self) -> None:
        project = self._current_project_or_warn()
        if project is None:
            return

        configuration = self._simulation_view.current_configuration()
        try:
            run_record = self._context.simulation_service.start_simulation(
                project,
                configuration,
            )
        except SimulationPreparationError as exc:
            self._simulation_view.set_validation_messages(
                [
                    f"{issue.severity.value}: {issue.path} - {issue.message}"
                    for issue in exc.validation.issues
                ]
            )
            QMessageBox.warning(self, "Start Run", str(exc))
            return
        except Exception as exc:
            LOGGER.exception("Failed to start simulation")
            QMessageBox.warning(self, "Start Run", str(exc))
            return

        self.refresh_views()
        self.statusBar().showMessage(
            f"Started run {run_record.run_id}",
            6000,
        )

    def _on_cancel_run(self) -> None:
        cancelled = self._context.simulation_service.cancel_simulation()
        if cancelled:
            self.statusBar().showMessage("Cancellation requested.", 5000)
        else:
            QMessageBox.information(
                self,
                "Cancel Run",
                "There is no active run to cancel.",
            )

    def _on_open_run_directory(self) -> None:
        run_record = self._resolve_target_run()
        if run_record is None:
            QMessageBox.information(
                self,
                "Open Run Folder",
                "Select a run from the history or start a run first.",
            )
            return
        path = self._context.simulation_service.open_run_directory(run_record)
        if path is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _on_open_output_directory(self) -> None:
        run_record = self._resolve_target_run()
        if run_record is None:
            QMessageBox.information(
                self,
                "Open Output Folder",
                "Select a run from the history or start a run first.",
            )
            return
        path = self._context.simulation_service.open_output_directory(run_record)
        if path is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _refresh_simulation_runtime_state(self) -> None:
        project = self._context.workspace_service.state.current_project
        if project is None:
            self._simulation_view.set_run_state(None, [])
            self._simulation_view.set_log_output("")
            return

        state = self._context.workspace_service.state
        history = state.run_history
        active_run = self._context.simulation_service.get_run_status()
        target_run = self._resolve_target_run(default_to_active=True)
        log_snapshot = self._context.simulation_service.get_log_snapshot_for_run(target_run)

        self._simulation_view.set_run_state(active_run, history)
        self._simulation_view.set_log_output(log_snapshot.combined_text)
        self._update_window_title()

    def _resolve_target_run(
        self,
        *,
        default_to_active: bool = False,
    ) -> SimulationRunRecord | None:
        selected_run_id = self._simulation_view.selected_run_id()
        for record in self._context.workspace_service.state.run_history:
            if selected_run_id and record.run_id == selected_run_id:
                return record

        if default_to_active:
            active_run = self._context.workspace_service.state.active_run
            if active_run is not None:
                return active_run
            history = self._context.workspace_service.state.run_history
            if history:
                return history[0]
        return None

    def _current_project_or_warn(self):
        project = self._context.workspace_service.state.current_project
        if project is not None:
            return project
        QMessageBox.information(
            self,
            "Simulation",
            "Create or open a project before using the simulation runner.",
        )
        return None

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About GPRMax Workbench",
            "Stage 4 foundation: form-based model editor MVP on top of Stage 3 input generation and subprocess execution.",
        )
