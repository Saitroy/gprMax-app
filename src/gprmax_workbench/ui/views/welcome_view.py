from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
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
    recent_project_requested = Signal(str)
    example_project_requested = Signal(str)

    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._current_project: Project | None = None
        self._example_projects: list[ExampleProjectItem] = []

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._new_button = QPushButton()
        self._new_button.setObjectName("PrimaryButton")
        self._new_button.clicked.connect(self.new_project_requested.emit)
        self._open_button = QPushButton()
        self._open_button.clicked.connect(self.open_project_requested.emit)

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
        hero_layout.addWidget(self._hero_eyebrow)
        hero_layout.addWidget(self._hero_title)
        hero_layout.addWidget(self._hero_body)
        hero_layout.addLayout(hero_actions)
        self._hero_card = hero

        self._current_project_label = QLabel()
        self._current_project_label.setWordWrap(True)
        self._current_card_heading = QLabel()
        self._current_card_heading.setObjectName("SectionTitle")
        self._current_card = self._build_card(
            self._current_card_heading,
            self._current_project_label,
        )

        self._workflow_card_heading = QLabel()
        self._workflow_card_heading.setObjectName("SectionTitle")
        self._workflow_description = QLabel()
        self._workflow_description.setWordWrap(True)
        self._workflow_steps: list[QLabel] = [QLabel() for _ in range(4)]
        workflow_content = QWidget()
        workflow_layout = QVBoxLayout(workflow_content)
        workflow_layout.setContentsMargins(0, 0, 0, 0)
        workflow_layout.setSpacing(8)
        workflow_layout.addWidget(self._workflow_description)
        for label in self._workflow_steps:
            label.setWordWrap(True)
            workflow_layout.addWidget(label)
        self._workflow_card = self._build_card(
            self._workflow_card_heading,
            workflow_content,
        )

        self._examples_card_heading = QLabel()
        self._examples_card_heading.setObjectName("SectionTitle")
        self._examples_description = QLabel()
        self._examples_description.setWordWrap(True)
        examples_content = QWidget()
        examples_layout = QVBoxLayout(examples_content)
        examples_layout.setContentsMargins(0, 0, 0, 0)
        examples_layout.setSpacing(8)
        examples_layout.addWidget(self._examples_description)
        self._example_actions = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        examples_layout.addLayout(self._example_actions)
        self._examples_card = self._build_card(
            self._examples_card_heading,
            examples_content,
        )

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
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._hero_card)
        layout.addWidget(self._dashboard, 1)

        self.retranslate_ui()
        self._reflow_cards()

    def set_current_project(self, project: Project | None) -> None:
        self._current_project = project
        if project is None:
            self._current_project_label.setText(self._localization.text("welcome.no_project"))
            return

        self._current_project_label.setText(
            self._localization.text(
                "welcome.current_project_details",
                name=project.metadata.name,
                path=project.root,
                model_title=project.model.title or self._localization.text("common.not_set"),
            )
        )

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
        self._clear_layout(self._example_actions)
        if not self._example_projects:
            empty_label = QLabel(self._localization.text("welcome.examples.none"))
            empty_label.setWordWrap(True)
            self._example_actions.addWidget(empty_label)
            return

        for item in self._example_projects:
            button = QPushButton(item.title)
            button.clicked.connect(
                lambda _checked=False, path=item.path: self.example_project_requested.emit(path)
            )
            button.setToolTip(item.description)
            self._example_actions.addWidget(button)

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
        self._current_card_heading.setText(self._localization.text("welcome.current_project"))
        self._workflow_card_heading.setText(self._localization.text("welcome.workflow.title"))
        self._workflow_description.setText(
            self._localization.text("welcome.workflow.description")
        )
        for index, label in enumerate(self._workflow_steps, start=1):
            label.setText(self._localization.text(f"welcome.workflow.step{index}"))
        self._examples_card_heading.setText(self._localization.text("welcome.examples.title"))
        self._examples_description.setText(
            self._localization.text("welcome.examples.description")
        )
        self._recent_card_heading.setText(self._localization.text("welcome.recent_projects"))
        self.set_current_project(self._current_project)
        self.set_example_projects(self._example_projects)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reflow_cards()

    def _reflow_cards(self) -> None:
        while self._dashboard_grid.count():
            item = self._dashboard_grid.takeAt(0)
            if item is not None:
                item.widget()

        wide = self.width() >= 1080
        if wide:
            self._dashboard_grid.addWidget(self._current_card, 0, 0)
            self._dashboard_grid.addWidget(self._workflow_card, 0, 1)
            self._dashboard_grid.addWidget(self._examples_card, 1, 0)
            self._dashboard_grid.addWidget(self._recent_card, 1, 1)
        else:
            self._dashboard_grid.addWidget(self._current_card, 0, 0)
            self._dashboard_grid.addWidget(self._workflow_card, 1, 0)
            self._dashboard_grid.addWidget(self._examples_card, 2, 0)
            self._dashboard_grid.addWidget(self._recent_card, 3, 0)

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

    def _clear_layout(self, layout: FlowLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
