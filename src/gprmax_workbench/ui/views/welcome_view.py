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

from ...domain.models import Project, RecentProject


class WelcomeView(QWidget):
    new_project_requested = Signal()
    open_project_requested = Signal()
    recent_project_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_project_label = QLabel("No project is currently open.")
        self._current_project_label.setWordWrap(True)
        self._recent_list = QListWidget()
        self._recent_list.itemActivated.connect(self._emit_recent_project)

        title = QLabel("Welcome")
        title.setObjectName("ViewTitle")

        subtitle = QLabel(
            "Create a new project, reopen an existing one, or continue from the recent "
            "projects list. This is the non-programmer entrypoint into the workflow."
        )
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        new_button = QPushButton("New Project")
        new_button.clicked.connect(self.new_project_requested.emit)

        open_button = QPushButton("Open Project")
        open_button.clicked.connect(self.open_project_requested.emit)

        button_row = QHBoxLayout()
        button_row.addWidget(new_button)
        button_row.addWidget(open_button)
        button_row.addStretch(1)

        current_card = self._build_card(
            "Current project",
            self._current_project_label,
        )
        recent_card = self._build_card("Recent projects", self._recent_list)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(button_row)
        layout.addWidget(current_card)
        layout.addWidget(recent_card, 1)

    def set_current_project(self, project: Project | None) -> None:
        if project is None:
            self._current_project_label.setText("No project is currently open.")
            return

        self._current_project_label.setText(
            f"{project.metadata.name}\n"
            f"Path: {project.root}\n"
            f"Model title: {project.model.title or 'Not set'}"
        )

    def set_recent_projects(self, recent_projects: Sequence[RecentProject]) -> None:
        self._recent_list.clear()
        if not recent_projects:
            item = QListWidgetItem("No recent projects yet.")
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

    def _build_card(self, title: str, content: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("ViewCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        heading = QLabel(title)
        heading.setObjectName("SectionTitle")

        layout.addWidget(heading)
        layout.addWidget(content)
        return card
