from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QScrollArea,
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
from .dialogs.settings_dialog import SettingsDialog
from .views.project_view import ProjectView
from .views.results_view import ResultsView
from .views.settings_view import SettingsView
from .views.simulation_view import SimulationView
from .views.welcome_view import ExampleProjectItem, WelcomeView

if TYPE_CHECKING:
    from ..app import ApplicationContext
    from ..domain.simulation import SimulationRunRecord

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PageSpec:
    title_key: str
    description_key: str
    widget: QWidget


class MainWindow(QMainWindow):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._localization = context.localization_service
        self._navigation = QListWidget()
        self._stack = QStackedWidget()
        self._simulation_refresh_timer = QTimer(self)
        self._simulation_refresh_timer.setInterval(400)
        self._simulation_refresh_timer.timeout.connect(self._refresh_simulation_runtime_state)

        self._welcome_view = WelcomeView(self._localization)
        self._project_view = ProjectView(
            localization=self._localization,
            model_editor_service=context.model_editor_service,
            validation_service=context.validation_service,
            input_preview_service=context.input_preview_service,
        )
        self._simulation_view = SimulationView(
            localization=self._localization,
            runtime_label=context.simulation_service.runtime_label(),
        )
        self._results_view = ResultsView(
            localization=self._localization,
            results_service=context.results_service,
            trace_service=context.trace_service,
            bscan_service=context.bscan_service,
        )
        self._settings_view = SettingsView(self._localization)
        self._settings_dialog = SettingsDialog(self._settings_view, self)
        self._pages = self._build_pages()
        self._page_index_by_title_key = {
            page.title_key: index for index, page in enumerate(self._pages)
        }
        self._navigation_page_indexes = list(range(len(self._pages)))
        self._last_polled_run_state: tuple[str, str] | None = None

        self._new_project_action = QAction(self)
        self._open_project_action = QAction(self)
        self._save_project_action = QAction(self)
        self._open_settings_action = QAction(self)
        self._about_action = QAction(self)
        self._file_menu = self.menuBar().addMenu("")
        self._settings_menu = self.menuBar().addMenu("")
        self._help_menu = self.menuBar().addMenu("")

        self.setWindowTitle(self._localization.text("window.title.base"))
        self.resize(1440, 920)

        self._connect_signals()
        self._create_actions()
        self._build_ui()
        self._apply_screen_adaptive_geometry()
        self._welcome_view.set_example_projects(self._discover_example_projects())
        self.retranslate_ui()
        self.refresh_views()
        self._simulation_refresh_timer.start()

    def _build_pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                title_key="page.welcome.title",
                description_key="page.welcome.description",
                widget=self._welcome_view,
            ),
            PageSpec(
                title_key="page.project.title",
                description_key="page.project.description",
                widget=self._project_view,
            ),
            PageSpec(
                title_key="page.simulation.title",
                description_key="page.simulation.description",
                widget=self._simulation_view,
            ),
            PageSpec(
                title_key="page.results.title",
                description_key="page.results.description",
                widget=self._results_view,
            ),
        ]

    def _connect_signals(self) -> None:
        self._welcome_view.new_project_requested.connect(self._on_new_project)
        self._welcome_view.open_project_requested.connect(self._on_open_project)
        self._welcome_view.recent_project_requested.connect(self._on_open_recent_project)
        self._welcome_view.example_project_requested.connect(self._on_open_example_project)
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
        self._new_project_action.triggered.connect(self._on_new_project)
        self._open_project_action.triggered.connect(self._on_open_project)
        self._save_project_action.triggered.connect(self._on_save_project)
        self._open_settings_action.triggered.connect(self._open_settings_page)
        self._about_action.triggered.connect(self._show_about_dialog)

        self._file_menu.addAction(self._new_project_action)
        self._file_menu.addAction(self._open_project_action)
        self._file_menu.addAction(self._save_project_action)
        self._settings_menu.addAction(self._open_settings_action)
        self._help_menu.addAction(self._about_action)

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        sidebar = self._build_sidebar()
        content = self._build_content_area()

        layout.addWidget(sidebar, 0)
        layout.addWidget(content, 1)

        self.setCentralWidget(central)
        self.statusBar().showMessage(self._localization.text("status.stage_ready"))

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
            self._last_polled_run_state = None

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
            runtime_info=self._context.runtime_service.runtime_info(),
        )
        self._results_view.refresh_project(project.root if project is not None else None)
        self._refresh_welcome_summary()
        self._simulation_view.set_runtime_label(
            self._context.simulation_service.runtime_label()
        )
        self._save_project_action.setEnabled(project is not None)
        self._update_window_title()
        self._refresh_simulation_runtime_state()

    def retranslate_ui(self) -> None:
        self._file_menu.setTitle(self._localization.text("menu.file"))
        self._settings_menu.setTitle(self._localization.text("menu.settings"))
        self._help_menu.setTitle(self._localization.text("menu.help"))
        self._new_project_action.setText(self._localization.text("action.new_project"))
        self._open_project_action.setText(self._localization.text("action.open_project"))
        self._save_project_action.setText(self._localization.text("action.save_project"))
        self._open_settings_action.setText(self._localization.text("action.open_settings"))
        self._about_action.setText(self._localization.text("action.about"))
        self._sidebar_title.setText(self._localization.text("sidebar.title"))
        self._sidebar_subtitle.setText(self._localization.text("sidebar.subtitle"))
        self._retranslate_navigation()
        self._welcome_view.retranslate_ui()
        self._project_view.retranslate_ui()
        self._simulation_view.retranslate_ui()
        self._results_view.retranslate_ui()
        self._settings_view.retranslate_ui()
        self._settings_dialog.retranslate_ui(self._localization.text("settings.title"))
        self._welcome_view.set_example_projects(self._discover_example_projects())
        self._refresh_welcome_summary()
        self._update_window_title()

    def _retranslate_navigation(self) -> None:
        for row, page_index in enumerate(self._navigation_page_indexes):
            item = self._navigation.item(row)
            if item is None:
                continue
            page = self._pages[page_index]
            item.setText(self._localization.text(page.title_key))
            item.setToolTip(self._localization.text(page.description_key))

    def _refresh_shell_state(self) -> None:
        workspace = self._context.workspace_service
        project = workspace.state.current_project
        self._welcome_view.set_current_project(project)
        self._simulation_view.set_project_state(
            project_name=project.metadata.name if project else None,
            is_dirty=workspace.state.current_project_dirty,
        )
        self._save_project_action.setEnabled(project is not None)
        self._refresh_welcome_summary()
        self._update_window_title()

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("Sidebar")
        self._sidebar = frame
        frame.setFixedWidth(self._sidebar_width_for_window(self.width() or 1440))

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self._sidebar_title = QLabel()
        self._sidebar_title.setObjectName("AppTitle")
        self._sidebar_title.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self._sidebar_subtitle = QLabel()
        self._sidebar_subtitle.setObjectName("AppSubtitle")
        self._sidebar_subtitle.setWordWrap(True)

        self._navigation.setObjectName("Navigation")
        self._navigation.setSpacing(4)
        self._navigation.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        for page_index in self._navigation_page_indexes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, page_index)
            self._navigation.addItem(item)

        self._navigation.currentRowChanged.connect(self._on_navigation_changed)

        layout.addWidget(self._sidebar_title)
        layout.addWidget(self._sidebar_subtitle)
        layout.addSpacing(8)
        layout.addWidget(self._navigation)

        self._retranslate_navigation()
        return frame

    def _apply_screen_adaptive_geometry(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        target_width = min(1440, max(960, available.width() - 80))
        target_height = min(920, max(700, available.height() - 96))
        target_width = min(target_width, available.width())
        target_height = min(target_height, available.height())
        self.resize(target_width, target_height)
        self._sidebar.setFixedWidth(self._sidebar_width_for_window(target_width))

        centered_x = available.x() + max(0, (available.width() - target_width) // 2)
        centered_y = available.y() + max(0, (available.height() - target_height) // 2)
        self.move(centered_x, centered_y)

    def _sidebar_width_for_window(self, window_width: int) -> int:
        return max(220, min(300, int(window_width * 0.19)))

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_sidebar"):
            self._sidebar.setFixedWidth(self._sidebar_width_for_window(self.width()))

    def _build_content_stack(self) -> QWidget:
        for page in self._pages:
            scroll_area = QScrollArea()
            scroll_area.setObjectName("PageScrollArea")
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setWidget(page.widget)
            self._stack.addWidget(scroll_area)
        self._navigation.setCurrentRow(0)
        return self._stack

    def _build_content_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_content_stack(), 1)
        return container

    def _on_navigation_changed(self, row: int) -> None:
        item = self._navigation.item(row) if row >= 0 else None
        if item is None:
            return
        page_index = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(page_index, int):
            return
        self._show_page(page_index, sync_navigation=False)

    def _update_status(self, page_index: int) -> None:
        if page_index < 0 or page_index >= len(self._pages):
            return
        self.statusBar().showMessage(
            self._localization.text(self._pages[page_index].description_key)
        )

    def _show_page(self, page_index: int, *, sync_navigation: bool = True) -> None:
        self._stack.setCurrentIndex(page_index)
        if sync_navigation:
            row = (
                self._navigation_page_indexes.index(page_index)
                if page_index in self._navigation_page_indexes
                else -1
            )
            self._navigation.setCurrentRow(row)
        self._update_status(page_index)

    def _open_settings_page(self) -> None:
        self._settings_view.set_settings(
            settings=self._context.settings_service.settings,
            runtime_info=self._context.runtime_service.runtime_info(),
        )
        self._settings_dialog.retranslate_ui(self._localization.text("settings.title"))
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def _show_project_page(self) -> None:
        self._show_page(self._page_index_by_title_key["page.project.title"])

    def _show_results_page(self) -> None:
        self._show_page(self._page_index_by_title_key["page.results.title"])

    def _update_window_title(self) -> None:
        current_project = self._context.workspace_service.state.current_project
        active_run = self._context.workspace_service.state.active_run
        if current_project is None:
            self.setWindowTitle(self._localization.text("window.title.base"))
            return

        dirty_marker = "*" if self._context.workspace_service.state.current_project_dirty else ""
        run_suffix = ""
        if active_run is not None and active_run.status.value in {"preparing", "running"}:
            run_suffix = self._localization.text(
                "window.run_suffix",
                status=self._localization.simulation_status_text(active_run.status.value),
                run_id=active_run.run_id,
            )
        self.setWindowTitle(
            self._localization.text(
                "window.title.project",
                project_name=current_project.metadata.name,
                dirty_marker=dirty_marker,
                run_suffix=run_suffix,
            )
        )

    def _on_new_project(self) -> None:
        dialog = NewProjectDialog(self._localization, self)
        if dialog.exec() == 0:
            return

        try:
            project = self._context.workspace_service.create_project(
                root=dialog.project_root(),
                name=dialog.project_name(),
            )
        except Exception as exc:
            LOGGER.exception("Failed to create project")
            QMessageBox.critical(
                self,
                self._localization.text("message.new_project.title"),
                self._localization.translate_message(str(exc)),
            )
            return

        self.refresh_views()
        self._show_project_page()
        self.statusBar().showMessage(
            self._localization.text(
                "status.created_project",
                name=project.metadata.name,
                root=project.root,
            ),
            6000,
        )

    def _on_open_project(self) -> None:
        project_dir = QFileDialog.getExistingDirectory(
            self,
            self._localization.text("dialog.open_project_directory"),
            str(Path.home()),
        )
        if not project_dir:
            return

        self._open_project_at(Path(project_dir))

    def _on_open_recent_project(self, path: str) -> None:
        self._open_project_at(Path(path))

    def _on_open_example_project(self, path: str) -> None:
        self._open_project_at(Path(path))

    def _open_project_at(self, path: Path) -> None:
        try:
            project = self._context.workspace_service.open_project(path)
        except Exception as exc:
            LOGGER.exception("Failed to open project at %s", path)
            QMessageBox.critical(
                self,
                self._localization.text("message.open_project.title"),
                self._localization.translate_message(str(exc)),
            )
            return

        self.refresh_views()
        self._show_project_page()
        self.statusBar().showMessage(
            self._localization.text(
                "status.opened_project",
                name=project.metadata.name,
            ),
            6000,
        )

    def _on_save_project(self) -> None:
        if self._context.workspace_service.state.current_project is None:
            QMessageBox.information(
                self,
                self._localization.text("message.save_project.title"),
                self._localization.text("message.save_project.no_project"),
            )
            return

        try:
            validation = self._context.workspace_service.save_current_project()
        except ProjectValidationError as exc:
            QMessageBox.warning(
                self,
                self._localization.text("message.save_project.title"),
                "\n".join(
                    f"{issue.path}: {self._localization.translate_message(issue.message)}"
                    for issue in exc.validation.errors
                ),
            )
            return

        self.refresh_views()

        warning_text = ""
        if validation.warnings:
            warning_text = self._localization.text(
                "status.project_saved_warnings",
                warnings="; ".join(
                    self._localization.translate_message(issue.message)
                    for issue in validation.warnings
                ),
            )

        self.statusBar().showMessage(
            self._localization.text(
                "status.project_saved",
                warning_text=warning_text,
            ),
            8000,
        )

    def _on_project_editor_changed(self) -> None:
        self._refresh_shell_state()

    def _on_save_settings(self) -> None:
        settings = self._context.settings_service.update_preferences(
            advanced_mode=self._settings_view.advanced_mode_enabled(),
            gprmax_python_executable=self._settings_view.runtime_executable(),
            language=self._settings_view.selected_language(),
        )
        self._localization.set_language(settings.language)
        self._context.runtime_service.refresh()
        self.retranslate_ui()
        self.refresh_views()
        self.statusBar().showMessage(
            self._localization.text("status.settings_saved"),
            5000,
        )

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
            f"{self._localization.severity_text(issue.severity.value)}: "
            f"{issue.path} - {self._localization.translate_message(issue.message)}"
            for issue in validation.issues
        ]

        try:
            prepared = self._context.simulation_service.rebuild_input_preview(
                project,
                configuration,
            )
        except Exception as exc:
            LOGGER.exception("Failed to build input preview")
            QMessageBox.warning(
                self,
                self._localization.text("message.input_preview.title"),
                self._localization.translate_message(str(exc)),
            )
            return

        self._simulation_view.set_input_preview(prepared.preview_text)
        self._simulation_view.set_validation_messages(
            messages
            + [
                self._localization.translate_message(message)
                for message in prepared.validation_messages
            ]
        )
        self.statusBar().showMessage(
            self._localization.text("status.preview_rebuilt"),
            5000,
        )

    def _on_export_input(self) -> None:
        project = self._current_project_or_warn()
        if project is None:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            self._localization.text("dialog.export_input"),
            str(project.root / "generated" / "exported.in"),
            self._localization.text("dialog.export_input_filter"),
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
            QMessageBox.warning(
                self,
                self._localization.text("message.export_input.title"),
                self._localization.translate_message(str(exc)),
            )
            return

        self.statusBar().showMessage(
            self._localization.text(
                "status.input_exported",
                destination=destination,
            ),
            6000,
        )

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
                    f"{self._localization.severity_text(issue.severity.value)}: "
                    f"{issue.path} - {self._localization.translate_message(issue.message)}"
                    for issue in exc.validation.issues
                ]
            )
            QMessageBox.warning(
                self,
                self._localization.text("message.start_run.title"),
                "\n".join(
                    f"{issue.path}: {self._localization.translate_message(issue.message)}"
                    for issue in exc.validation.errors
                ),
            )
            return
        except Exception as exc:
            LOGGER.exception("Failed to start simulation")
            QMessageBox.warning(
                self,
                self._localization.text("message.start_run.title"),
                self._localization.translate_message(str(exc)),
            )
            return

        self.refresh_views()
        self.statusBar().showMessage(
            self._localization.text("status.run_started", run_id=run_record.run_id),
            6000,
        )

    def _on_cancel_run(self) -> None:
        cancelled = self._context.simulation_service.cancel_simulation()
        if cancelled:
            self.statusBar().showMessage(
                self._localization.text("status.cancellation_requested"),
                5000,
            )
        else:
            QMessageBox.information(
                self,
                self._localization.text("message.cancel_run.title"),
                self._localization.text("message.cancel_run.none"),
            )

    def _on_open_run_directory(self) -> None:
        run_record = self._resolve_target_run()
        if run_record is None:
            QMessageBox.information(
                self,
                self._localization.text("message.open_run_folder.title"),
                self._localization.text("message.open_run_folder.none"),
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
                self._localization.text("message.open_output_folder.title"),
                self._localization.text("message.open_output_folder.none"),
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
            self._results_view.refresh_project(None)
            self._last_polled_run_state = None
            return

        state = self._context.workspace_service.state
        history = state.run_history
        active_run = self._context.simulation_service.get_run_status()
        previous_run_state = self._last_polled_run_state
        current_run_state = (
            (active_run.run_id, active_run.status.value)
            if active_run is not None
            else None
        )
        target_run = self._resolve_target_run(default_to_active=True)
        log_snapshot = self._context.simulation_service.get_log_snapshot_for_run(target_run)

        self._simulation_view.set_run_state(active_run, history)
        self._simulation_view.set_log_output(log_snapshot.combined_text)
        self._results_view.refresh_project(project.root)
        self._refresh_welcome_summary()
        self._update_window_title()
        self._last_polled_run_state = current_run_state

        if (
            previous_run_state is not None
            and current_run_state is not None
            and previous_run_state[0] == current_run_state[0]
            and previous_run_state[1] in {"preparing", "running"}
            and current_run_state[1] == "completed"
        ):
            self._context.results_service.focus_run(active_run.run_id)
            self._results_view.refresh_project(project.root)
            self._show_results_page()

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
            self._localization.text("message.simulation.title"),
            self._localization.text("message.simulation.no_project"),
        )
        return None

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            self._localization.text("about.title"),
            self._localization.text("about.body"),
        )

    def _refresh_welcome_summary(self) -> None:
        workspace = self._context.workspace_service.state
        project = workspace.current_project
        if project is None:
            self._welcome_view.set_current_project(None)
            self._welcome_view.set_workspace_state(
                readiness_text=self._localization.text("welcome.status.no_project"),
                activity_text=self._localization.text("workspace.value.no_run"),
            )
            return

        validation = workspace.current_project_validation
        if validation.errors:
            readiness_state = self._localization.text(
                "workspace.value.validation_errors",
                errors=len(validation.errors),
                warnings=len(validation.warnings),
            )
        elif workspace.current_project_dirty:
            readiness_state = self._localization.text("welcome.status.unsaved")
        elif validation.warnings:
            readiness_state = self._localization.text(
                "workspace.value.validation_warnings",
                warnings=len(validation.warnings),
            )
        else:
            readiness_state = self._localization.text("workspace.value.validation_ready")

        if workspace.active_run is not None and workspace.active_run.status.value in {
            "preparing",
            "running",
        }:
            activity_state = self._localization.text(
                "workspace.value.run_active",
                run_id=workspace.active_run.run_id,
                status=self._localization.simulation_status_text(
                    workspace.active_run.status.value
                ),
            )
        elif workspace.run_history:
            latest = workspace.run_history[0]
            activity_state = self._localization.text(
                "workspace.value.run_last",
                run_id=latest.run_id,
                status=self._localization.simulation_status_text(latest.status.value),
            )
        else:
            activity_state = self._localization.text("workspace.value.no_run")

        self._welcome_view.set_current_project(project)
        self._welcome_view.set_workspace_state(
            readiness_text=readiness_state,
            activity_text=activity_state,
        )

    def _discover_example_projects(self) -> list[ExampleProjectItem]:
        repo_root = Path(__file__).resolve().parents[3]
        summary_path = repo_root / "examples" / "summary.json"
        if not summary_path.exists():
            return []

        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            LOGGER.exception("Failed to load example projects from %s", summary_path)
            return []

        projects = payload.get("projects", {})
        examples: list[ExampleProjectItem] = []
        for item in projects.values():
            if not isinstance(item, dict):
                continue
            project_root = item.get("project_root")
            if not isinstance(project_root, str):
                continue
            absolute_path = (summary_path.parent / project_root).resolve()
            if not absolute_path.exists():
                continue
            title = absolute_path.name.replace("_", " ").title()
            project_file = absolute_path / "project.gprwb.json"
            if project_file.exists():
                try:
                    project_payload = json.loads(project_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    project_payload = {}
                metadata_payload = project_payload.get("metadata", {})
                if isinstance(metadata_payload, dict):
                    title = str(metadata_payload.get("name", title))
            examples.append(
                ExampleProjectItem(
                    title=title,
                    description=str(item.get("notes", "")),
                    path=str(absolute_path),
                )
            )
        return examples
