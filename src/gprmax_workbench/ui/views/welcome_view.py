from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ...application.services.localization_service import LocalizationService
from ...domain.models import Project, RecentProject
from ..layouts.flow_layout import FlowLayout


@dataclass(frozen=True, slots=True)
class ExampleProjectItem:
    title: str
    description: str
    path: str


class WelcomeView(QWidget):
    new_project_requested = Signal()
    open_project_requested = Signal()
    documentation_requested = Signal()
    recent_project_requested = Signal(str)

    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._current_project: Project | None = None
        self._example_projects: list[ExampleProjectItem] = []
        self._readiness_text = ""
        self._activity_text = ""

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)
        self._workflow_info_button = QToolButton()
        self._workflow_info_button.setObjectName("InfoButton")
        self._workflow_info_button.setAutoRaise(False)
        self._workflow_info_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._workflow_info_button.clicked.connect(self._show_workflow_help)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)
        header_row.addWidget(self._title)
        header_row.addWidget(self._workflow_info_button, 0, Qt.AlignmentFlag.AlignTop)
        header_row.addStretch(1)

        self._new_button = QPushButton()
        self._new_button.setObjectName("PrimaryButton")
        self._new_button.clicked.connect(self.new_project_requested.emit)
        self._open_button = QPushButton()
        self._open_button.clicked.connect(self.open_project_requested.emit)
        self._documentation_button = QPushButton()
        self._documentation_button.clicked.connect(self.documentation_requested.emit)

        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(10)
        self._hero_eyebrow = QLabel()
        self._hero_eyebrow.setObjectName("HeroEyebrow")
        self._hero_title = QLabel()
        self._hero_title.setObjectName("HeroTitle")
        self._hero_body = QLabel()
        self._hero_body.setObjectName("HeroBody")
        self._hero_body.setWordWrap(True)
        hero_actions = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        hero_actions.addWidget(self._new_button)
        hero_actions.addWidget(self._open_button)
        hero_actions.addWidget(self._documentation_button)
        hero_layout.addWidget(self._hero_eyebrow)
        hero_layout.addWidget(self._hero_title)
        hero_layout.addWidget(self._hero_body)
        hero_layout.addLayout(hero_actions)
        self._hero_card = hero

        self._status_heading = QLabel()
        self._status_heading.setObjectName("SectionTitle")
        self._status_project = QLabel()
        self._status_project.setWordWrap(True)
        self._status_readiness = QLabel()
        self._status_readiness.setWordWrap(True)
        self._status_activity = QLabel()
        self._status_activity.setWordWrap(True)
        status_content = QWidget()
        status_layout = QVBoxLayout(status_content)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        status_layout.addWidget(self._status_project)
        status_layout.addWidget(self._status_readiness)
        status_layout.addWidget(self._status_activity)
        self._status_card = self._build_card(self._status_heading, status_content)

        self._recent_list = QListWidget()
        self._recent_list.itemActivated.connect(self._emit_recent_project)
        self._recent_card_heading = QLabel()
        self._recent_card_heading.setObjectName("SectionTitle")
        self._recent_card = self._build_card(self._recent_card_heading, self._recent_list)

        self._dashboard = QWidget()
        self._dashboard_grid = QGridLayout(self._dashboard)
        self._dashboard_grid.setContentsMargins(0, 0, 0, 0)
        self._dashboard_grid.setSpacing(16)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addLayout(header_row)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._hero_card)
        layout.addWidget(self._dashboard, 1)

        self.retranslate_ui()
        self._reflow_cards()

    def set_current_project(self, project: Project | None) -> None:
        self._current_project = project
        self._refresh_project_status()

    def set_workspace_state(
        self,
        *,
        readiness_text: str,
        activity_text: str,
    ) -> None:
        self._readiness_text = readiness_text
        self._activity_text = activity_text
        self._refresh_project_status()

    def set_recent_projects(self, recent_projects: Sequence[RecentProject]) -> None:
        self._recent_list.clear()
        if not recent_projects:
            item = QListWidgetItem(self._localization.text("welcome.no_recent_projects"))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._recent_list.addItem(item)
            return

        for project in recent_projects:
            item = QListWidgetItem(f"{project.name}\n{project.path}")
            item.setData(Qt.ItemDataRole.UserRole, str(project.path))
            item.setToolTip(project.last_opened_at.isoformat())
            self._recent_list.addItem(item)

    def set_example_projects(
        self,
        examples: Sequence[ExampleProjectItem],
    ) -> None:
        self._example_projects = list(examples)

    def _emit_recent_project(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(path, str) and path:
            self.recent_project_requested.emit(path)

    def retranslate_ui(self) -> None:
        self._title.setText(self._localization.text("welcome.title"))
        self._subtitle.setText(self._localization.text("welcome.subtitle"))
        self._hero_eyebrow.setText(self._localization.text("welcome.hero.eyebrow"))
        self._hero_title.setText(self._localization.text("welcome.hero.title"))
        self._hero_body.setText(self._localization.text("welcome.hero.body"))
        self._new_button.setText(self._localization.text("action.new_project"))
        self._open_button.setText(self._localization.text("action.open_project"))
        self._documentation_button.setText(
            self._localization.text("action.open_documentation")
        )
        self._status_heading.setText(self._localization.text("welcome.status.title"))
        self._recent_card_heading.setText(self._localization.text("welcome.recent_projects"))
        self._workflow_info_button.setText(self._localization.text("welcome.workflow.info"))
        self._workflow_info_button.setToolTip(self._workflow_help_text())
        self._refresh_project_status()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reflow_cards()

    def _refresh_project_status(self) -> None:
        if self._current_project is None:
            self._status_project.setText(
                self._localization.text("welcome.status.empty_project")
            )
            self._status_readiness.setText(
                self._localization.text(
                    "welcome.status.readiness_line",
                    value=(
                        self._readiness_text
                        or self._localization.text("welcome.status.no_project")
                    ),
                )
            )
            self._status_activity.setText(
                self._localization.text("welcome.status.activity_line", value=self._activity_text or self._localization.text("workspace.value.no_run"))
            )
            return

        self._status_project.setText(
            self._localization.text(
                "welcome.status.project_line",
                name=self._current_project.metadata.name,
                path=self._current_project.root,
            )
        )
        self._status_readiness.setText(
            self._localization.text(
                "welcome.status.readiness_line",
                value=self._readiness_text or self._localization.text("workspace.value.validation_ready"),
            )
        )
        self._status_activity.setText(
            self._localization.text(
                "welcome.status.activity_line",
                value=self._activity_text or self._localization.text("workspace.value.no_run"),
            )
        )

    def _reflow_cards(self) -> None:
        while self._dashboard_grid.count():
            item = self._dashboard_grid.takeAt(0)
            if item is not None:
                item.widget()

        if self.width() >= 980:
            self._dashboard_grid.addWidget(self._status_card, 0, 0)
            self._dashboard_grid.addWidget(self._recent_card, 0, 1)
        else:
            self._dashboard_grid.addWidget(self._status_card, 0, 0)
            self._dashboard_grid.addWidget(self._recent_card, 1, 0)

        self._dashboard_grid.setColumnStretch(0, 1)
        self._dashboard_grid.setColumnStretch(1, 1)

    def _build_card(self, heading: QLabel, content: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("ViewCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        layout.addWidget(heading)
        layout.addWidget(content)
        return card

    def _workflow_help_text(self) -> str:
        return "\n".join(
            [
                self._localization.text("welcome.workflow.title"),
                self._localization.text("welcome.workflow.description"),
                self._localization.text("welcome.workflow.step1"),
                self._localization.text("welcome.workflow.step2"),
                self._localization.text("welcome.workflow.step3"),
                self._localization.text("welcome.workflow.step4"),
            ]
        )

    def _show_workflow_help(self) -> None:
        QToolTip.showText(
            self._workflow_info_button.mapToGlobal(self._workflow_info_button.rect().bottomLeft()),
            self._workflow_help_text(),
            self._workflow_info_button,
        )
