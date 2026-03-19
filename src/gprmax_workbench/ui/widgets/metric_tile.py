from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class MetricTile(QFrame):
    """Compact information tile for dashboard-like summaries."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricTile")

        self._eyebrow = QLabel()
        self._eyebrow.setObjectName("MetricEyebrow")
        self._value = QLabel()
        self._value.setObjectName("MetricValue")
        self._value.setWordWrap(True)
        self._caption = QLabel()
        self._caption.setObjectName("MetricCaption")
        self._caption.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        layout.addWidget(self._eyebrow)
        layout.addWidget(self._value)
        layout.addWidget(self._caption)

    def set_content(
        self,
        *,
        eyebrow: str,
        value: str,
        caption: str = "",
    ) -> None:
        self._eyebrow.setText(eyebrow)
        self._value.setText(value)
        self._caption.setText(caption)
        self._caption.setVisible(bool(caption))
