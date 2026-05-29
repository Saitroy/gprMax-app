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
    example_project_requested = Signal(str)
    settings_requested = Signal()

    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._current_project: Project | None = None
        self._recent_projects: list[RecentProject] = []
        self._example_projects: list[ExampleProjectItem] = []
        self._readiness_text = ""
        self._activity_text = ""
        self._runtime_text = ""
        self._runtime_detail = ""
        self._runtime_tone = "neutral"

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
        self._open_button.setProperty("buttonRole", "secondary")
        self._open_button.clicked.connect(self.open_project_requested.emit)
        self._documentation_button = QPushButton()
        self._documentation_button.setProperty("buttonRole", "ghost")
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
        self._status_project.setObjectName("StatusBadge")
        self._status_project.setProperty("statusTone", "neutral")
        self._status_project.setWordWrap(True)
        self._status_readiness = QLabel()
        self._status_readiness.setObjectName("StatusBadge")
        self._status_readiness.setProperty("statusTone", "neutral")
        self._status_readiness.setWordWrap(True)
        self._status_activity = QLabel()
        self._status_activity.setObjectName("StatusBadge")
        self._status_activity.setProperty("statusTone", "neutral")
        self._status_activity.setWordWrap(True)
        status_content = QWidget()
        status_layout = QVBoxLayout(status_content)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        status_layout.addWidget(self._status_project)
        status_layout.addWidget(self._status_readiness)
        status_layout.addWidget(self._status_activity)
        self._status_card = self._build_card(self._status_heading, status_content)

        self._runtime_heading = QLabel()
        self._runtime_heading.setObjectName("SectionTitle")
        self._runtime_status = QLabel()
        self._runtime_status.setObjectName("StatusBadge")
        self._runtime_status.setProperty("statusTone", "neutral")
        self._runtime_status.setWordWrap(True)
        self._runtime_detail_label = QLabel()
        self._runtime_detail_label.setObjectName("SectionBody")
        self._runtime_detail_label.setWordWrap(True)
        self._runtime_settings_button = QPushButton()
        self._runtime_settings_button.setProperty("buttonRole", "ghost")
        self._runtime_settings_button.clicked.connect(self.settings_requested.emit)
        runtime_content = QWidget()
        runtime_layout = QVBoxLayout(runtime_content)
        runtime_layout.setContentsMargins(0, 0, 0, 0)
        runtime_layout.setSpacing(8)
        runtime_layout.addWidget(self._runtime_status)
        runtime_layout.addWidget(self._runtime_detail_label)
        runtime_layout.addWidget(
            self._runtime_settings_button,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        self._runtime_card = self._build_card(self._runtime_heading, runtime_content)

        self._recent_list = QListWidget()
        self._recent_list.setObjectName("RecentProjectsList")
        self._recent_list.itemActivated.connect(self._emit_recent_project)
        self._recent_card_heading = QLabel()
        self._recent_card_heading.setObjectName("SectionTitle")
        self._recent_card = self._build_card(self._recent_card_heading, self._recent_list)

        self._examples_heading = QLabel()
        self._examples_heading.setObjectName("SectionTitle")
        self._examples_body = QLabel()
        self._examples_body.setObjectName("SectionBody")
        self._examples_body.setWordWrap(True)
        self._examples_content = QWidget()
        self._examples_layout = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        examples_content_layout = QVBoxLayout(self._examples_content)
        examples_content_layout.setContentsMargins(0, 0, 0, 0)
        examples_content_layout.setSpacing(10)
        examples_content_layout.addWidget(self._examples_body)
        examples_content_layout.addLayout(self._examples_layout)
        self._examples_card = self._build_card(
            self._examples_heading,
            self._examples_content,
        )

        self._quick_start_heading = QLabel()
        self._quick_start_heading.setObjectName("SectionTitle")
        self._quick_start_body = QLabel()
        self._quick_start_body.setObjectName("SectionBody")
        self._quick_start_body.setWordWrap(True)
        self._quick_start_card = self._build_card(
            self._quick_start_heading,
            self._quick_start_body,
        )
        self._quick_start_card.setVisible(False)

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

    def set_runtime_status(self, *, text: str, detail: str, tone: str) -> None:
        self._runtime_text = text
        self._runtime_detail = detail
        self._runtime_tone = tone
        self._refresh_runtime_status()

    def set_recent_projects(self, recent_projects: Sequence[RecentProject]) -> None:
        self._recent_projects = list(recent_projects)
        self._refresh_recent_projects()

    def _refresh_recent_projects(self) -> None:
        self._recent_list.clear()
        if not self._recent_projects:
            item = QListWidgetItem(self._localization.text("welcome.no_recent_projects"))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._recent_list.addItem(item)
            return

        for project in self._recent_projects:
            path_exists = project.path.exists()
            state_text = self._localization.text(
                "welcome.recent.available" if path_exists else "welcome.recent.missing"
            )
            opened_at = project.last_opened_at.strftime("%Y-%m-%d %H:%M")
            item = QListWidgetItem(
                self._localization.text(
                    "welcome.recent.item",
                    name=project.name,
                    path=project.path,
                    opened_at=opened_at,
                    state=state_text,
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, str(project.path))
            item.setToolTip(str(project.path))
            self._recent_list.addItem(item)

    def set_example_projects(
        self,
        examples: Sequence[ExampleProjectItem],
    ) -> None:
        self._example_projects = list(examples)
        self._refresh_examples()

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
        self._runtime_heading.setText(self._localization.text("welcome.runtime.title"))
        self._runtime_settings_button.setText(
            self._localization.text("welcome.runtime.settings_action")
        )
        self._recent_card_heading.setText(self._localization.text("welcome.recent_projects"))
        self._examples_heading.setText(self._localization.text("welcome.examples.title"))
        self._examples_body.setText(self._localization.text("welcome.examples.description"))
        self._quick_start_heading.setText(self._localization.text("welcome.quick_start.title"))
        self._quick_start_body.setText(self._quick_start_text())
        self._workflow_info_button.setText(self._localization.text("welcome.workflow.info"))
        self._workflow_info_button.setToolTip(self._workflow_help_text())
        self._refresh_project_status()
        self._refresh_runtime_status()
        self._refresh_recent_projects()
        self._refresh_examples()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reflow_cards()

    def _refresh_project_status(self) -> None:
        if self._current_project is None:
            self._set_status_badge(
                self._status_project,
                self._localization.text("welcome.status.empty_project"),
                "neutral",
            )
            readiness_text = self._localization.text(
                "welcome.status.readiness_line",
                value=(
                    self._readiness_text
                    or self._localization.text("welcome.status.no_project")
                ),
            )
            self._set_status_badge(
                self._status_readiness,
                readiness_text,
                self._readiness_tone(readiness_text),
            )
            activity_text = self._localization.text(
                "welcome.status.activity_line",
                value=(
                    self._activity_text
                    or self._localization.text("workspace.value.no_run")
                ),
            )
            self._set_status_badge(
                self._status_activity,
                activity_text,
                self._activity_tone(activity_text),
            )
            return

        self._set_status_badge(
            self._status_project,
            self._localization.text(
                "welcome.status.project_line",
                name=self._current_project.metadata.name,
                path=self._current_project.root,
            ),
            "info",
        )
        readiness_text = self._localization.text(
            "welcome.status.readiness_line",
            value=(
                self._readiness_text
                or self._localization.text("workspace.value.validation_ready")
            ),
        )
        self._set_status_badge(
            self._status_readiness,
            readiness_text,
            self._readiness_tone(readiness_text),
        )
        activity_text = self._localization.text(
            "welcome.status.activity_line",
            value=(
                self._activity_text
                or self._localization.text("workspace.value.no_run")
            ),
        )
        self._set_status_badge(
            self._status_activity,
            activity_text,
            self._activity_tone(activity_text),
        )

    def _refresh_runtime_status(self) -> None:
        text = self._runtime_text or self._localization.text("welcome.runtime.pending")
        detail = self._runtime_detail or self._localization.text(
            "welcome.runtime.pending_detail"
        )
        self._set_status_badge(self._runtime_status, text, self._runtime_tone)
        self._runtime_detail_label.setText(detail)

    def _refresh_examples(self) -> None:
        while self._examples_layout.count():
            item = self._examples_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self._example_projects:
            empty_label = QLabel(self._localization.text("welcome.examples.none"))
            empty_label.setObjectName("SectionBody")
            empty_label.setWordWrap(True)
            self._examples_layout.addWidget(empty_label)
            return

        for example in self._example_projects:
            button = QPushButton(example.title)
            button.setProperty("buttonRole", "projectCard")
            button.setToolTip(example.description)
            button.clicked.connect(
                lambda _checked=False, path=example.path: self._emit_example_project(path)
            )
            self._examples_layout.addWidget(button)

    def _emit_example_project(self, path: str) -> None:
        self.example_project_requested.emit(path)

    def _set_status_badge(self, label: QLabel, text: str, tone: str) -> None:
        label.setText(text)
        label.setToolTip(text)
        label.setProperty("statusTone", tone)
        style = label.style()
        style.unpolish(label)
        style.polish(label)
        label.update()

    def _readiness_tone(self, text: str) -> str:
        normalized = text.casefold()
        if any(
            token in normalized
            for token in ("no project", "open a project", "откройте проект", "сначала")
        ):
            return "neutral"
        if any(
            token in normalized
            for token in (
                "error",
                "errors",
                "ошиб",
                "not ready",
                "не готов",
            )
        ):
            return "error"
        if any(
            token in normalized
            for token in (
                "warning",
                "warnings",
                "предупреж",
                "unsaved",
                "несохран",
            )
        ):
            return "warning"
        if any(token in normalized for token in ("ready", "готов")):
            return "success"
        return "info"

    def _activity_tone(self, text: str) -> str:
        normalized = text.casefold()
        if any(token in normalized for token in ("failed", "ошиб", "error")):
            return "error"
        if any(token in normalized for token in ("cancel", "отмен")):
            return "warning"
        if any(token in normalized for token in ("completed", "заверш")):
            return "success"
        if any(
            token in normalized
            for token in (
                "no run",
                "нет запуск",
                "запусков нет",
                "не запуск",
            )
        ):
            return "neutral"
        return "info"

    def _reflow_cards(self) -> None:
        while self._dashboard_grid.count():
            item = self._dashboard_grid.takeAt(0)
            if item is not None:
                item.widget()

        if self.width() >= 1040:
            self._dashboard_grid.addWidget(self._status_card, 0, 0)
            self._dashboard_grid.addWidget(self._runtime_card, 0, 1)
            self._dashboard_grid.addWidget(self._recent_card, 1, 0)
            self._dashboard_grid.addWidget(self._examples_card, 1, 1)
        else:
            self._dashboard_grid.addWidget(self._status_card, 0, 0)
            self._dashboard_grid.addWidget(self._runtime_card, 1, 0)
            self._dashboard_grid.addWidget(self._recent_card, 2, 0)
            self._dashboard_grid.addWidget(self._examples_card, 3, 0)

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

    def _quick_start_text(self) -> str:
        return "\n".join(
            [
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
