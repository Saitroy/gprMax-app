from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class SectionCard(QFrame):
    def __init__(self, title: str, body: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        heading = QLabel(title)
        heading.setObjectName("SectionTitle")

        text = QLabel(body)
        text.setObjectName("SectionBody")
        text.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(text)


class PlaceholderView(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str,
        sections: Sequence[tuple[str, str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        heading = QLabel(title)
        heading.setObjectName("ViewTitle")

        text = QLabel(subtitle)
        text.setObjectName("ViewSubtitle")
        text.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(text)

        for section_title, body in sections:
            layout.addWidget(SectionCard(section_title, body))

        layout.addStretch(1)
