from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...application.services.localization_service import LocalizationService
from ..layouts.flow_layout import FlowLayout
from ..views.welcome_view import ExampleProjectItem


class DocumentationDialog(QDialog):
    example_project_requested = Signal(str)

    def __init__(
        self,
        *,
        localization: LocalizationService,
        repo_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._repo_root = repo_root
        self._examples: list[ExampleProjectItem] = []

        self.setModal(False)
        self.resize(760, 520)

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._readme_button = QPushButton()
        self._readme_button.clicked.connect(
            lambda: self._open_path(self._repo_root / "README.md")
        )
        self._docs_button = QPushButton()
        self._docs_button.clicked.connect(lambda: self._open_path(self._repo_root / "docs"))
        self._examples_button = QPushButton()
        self._examples_button.clicked.connect(
            lambda: self._open_path(self._repo_root / "examples")
        )

        actions = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        actions.addWidget(self._readme_button)
        actions.addWidget(self._docs_button)
        actions.addWidget(self._examples_button)

        self._examples_heading = QLabel()
        self._examples_heading.setObjectName("SectionTitle")
        self._examples_body = QLabel()
        self._examples_body.setObjectName("SectionBody")
        self._examples_body.setWordWrap(True)
        self._examples_actions = FlowLayout(horizontal_spacing=10, vertical_spacing=10)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addLayout(actions)
        layout.addWidget(self._examples_heading)
        layout.addWidget(self._examples_body)
        layout.addLayout(self._examples_actions)
        layout.addStretch(1)

        self.retranslate_ui()

    def set_examples(self, examples: Sequence[ExampleProjectItem]) -> None:
        self._examples = list(examples)
        while self._examples_actions.count():
            item = self._examples_actions.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self._examples:
            label = QLabel(self._localization.text("documentation.examples.none"))
            label.setObjectName("SectionBody")
            label.setWordWrap(True)
            self._examples_actions.addWidget(label)
            return

        for example in self._examples:
            button = QPushButton(example.title)
            button.setToolTip(example.description)
            button.clicked.connect(
                lambda _checked=False, path=example.path: self._open_example(path)
            )
            self._examples_actions.addWidget(button)

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self._localization.text("documentation.window_title"))
        self._title.setText(self._localization.text("documentation.title"))
        self._subtitle.setText(self._localization.text("documentation.subtitle"))
        self._readme_button.setText(self._localization.text("documentation.open_readme"))
        self._docs_button.setText(self._localization.text("documentation.open_docs"))
        self._examples_button.setText(
            self._localization.text("documentation.open_examples_folder")
        )
        self._examples_heading.setText(self._localization.text("documentation.examples.title"))
        self._examples_body.setText(self._localization.text("documentation.examples.body"))
        self.set_examples(self._examples)

    def _open_path(self, path: Path) -> None:
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_example(self, path: str) -> None:
        self.example_project_requested.emit(path)
        self.close()
