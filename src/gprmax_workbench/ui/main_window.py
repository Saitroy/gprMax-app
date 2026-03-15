from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
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

from .views.project_view import ProjectView
from .views.results_view import ResultsView
from .views.settings_view import SettingsView
from .views.simulation_view import SimulationView
from .views.welcome_view import WelcomeView


@dataclass(frozen=True, slots=True)
class PageSpec:
    title: str
    description: str
    factory: Callable[[], QWidget]


class MainWindow(QMainWindow):
    def __init__(self, context: object) -> None:
        super().__init__()
        self._context = context
        self._navigation = QListWidget()
        self._stack = QStackedWidget()
        self._pages = self._build_pages()

        self.setWindowTitle("GPRMax Workbench")
        self.resize(1360, 860)

        self._create_actions()
        self._build_ui()

    def _build_pages(self) -> list[PageSpec]:
        settings_service = self._context.settings_service
        simulation_service = self._context.simulation_service

        return [
            PageSpec(
                title="Welcome",
                description="Project manager and onboarding entrypoint.",
                factory=lambda: WelcomeView(
                    recent_projects=settings_service.recent_projects()
                ),
            ),
            PageSpec(
                title="Model Editor",
                description="Forms and visual workflows for model setup.",
                factory=ProjectView,
            ),
            PageSpec(
                title="Simulation",
                description="Run preparation, execution, and logs.",
                factory=lambda: SimulationView(
                    runtime_label=simulation_service.runtime_label()
                ),
            ),
            PageSpec(
                title="Results",
                description="Run outputs and viewer entrypoints.",
                factory=ResultsView,
            ),
            PageSpec(
                title="Settings",
                description="Application and runtime settings.",
                factory=lambda: SettingsView(
                    summary=settings_service.runtime_summary()
                ),
            ),
        ]

    def _create_actions(self) -> None:
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(
            lambda: self.statusBar().showMessage(
                "Project wizard will be implemented in Stage 2.", 5000
            )
        )

        open_project_action = QAction("Open Project", self)
        open_project_action.triggered.connect(
            lambda: self.statusBar().showMessage(
                "Project open flow will be implemented in Stage 2.", 5000
            )
        )

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)

        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(new_project_action)
        file_menu.addAction(open_project_action)

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
            "Architecture shell ready. Core workflows land in later stages."
        )

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
        self._navigation.setCurrentRow(0)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self._navigation)

        return frame

    def _build_content_stack(self) -> QWidget:
        for page in self._pages:
            self._stack.addWidget(page.factory())
        return self._stack

    def _update_status(self, index: int) -> None:
        if index < 0 or index >= len(self._pages):
            return
        self.statusBar().showMessage(self._pages[index].description)

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About GPRMax Workbench",
            "Stage 1 skeleton: PySide6 shell, layered architecture, and gprMax adapter scaffolding.",
        )
