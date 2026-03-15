from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...application.services.localization_service import LocalizationService
from ...domain.models import Project, RecentProject


class WelcomeView(QWidget):
    new_project_requested = Signal()
    open_project_requested = Signal()
    recent_project_requested = Signal(str)

    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._current_project: Project | None = None

        self._current_project_label = QLabel()
        self._current_project_label.setWordWrap(True)
        self._recent_list = QListWidget()
        self._recent_list.itemActivated.connect(self._emit_recent_project)

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")

        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._new_button = QPushButton()
        self._new_button.clicked.connect(self.new_project_requested.emit)

        self._open_button = QPushButton()
        self._open_button.clicked.connect(self.open_project_requested.emit)

        button_row = QHBoxLayout()
        button_row.addWidget(self._new_button)
        button_row.addWidget(self._open_button)
        button_row.addStretch(1)

        self._current_card_heading = QLabel()
        self._current_card_heading.setObjectName("SectionTitle")
        self._recent_card_heading = QLabel()
        self._recent_card_heading.setObjectName("SectionTitle")

        current_card = self._build_card(self._current_card_heading, self._current_project_label)
        recent_card = self._build_card(self._recent_card_heading, self._recent_list)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addLayout(button_row)
        layout.addWidget(current_card)
        layout.addWidget(recent_card, 1)

        self.retranslate_ui()

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

    def _emit_recent_project(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(path, str) and path:
            self.recent_project_requested.emit(path)

    def retranslate_ui(self) -> None:
        self._title.setText(self._localization.text("welcome.title"))
        self._subtitle.setText(self._localization.text("welcome.subtitle"))
        self._new_button.setText(self._localization.text("action.new_project"))
        self._open_button.setText(self._localization.text("action.open_project"))
        self._current_card_heading.setText(self._localization.text("welcome.current_project"))
        self._recent_card_heading.setText(self._localization.text("welcome.recent_projects"))
        self.set_current_project(self._current_project)

    def _build_card(self, heading: QLabel, content: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("ViewCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        layout.addWidget(heading)
        layout.addWidget(content)
        return card
