from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .shared import SectionCard


class SimulationView(QWidget):
    def __init__(self, runtime_label: str, parent=None) -> None:
        super().__init__(parent)
        self._runtime_card = SectionCard("Runtime adapter", runtime_label)

        title = QLabel("Simulation Runner")
        title.setObjectName("ViewTitle")

        subtitle = QLabel(
            "Stage 3 will add run orchestration, queueing, logs, and cancellation. "
            "Stage 2 only keeps the runtime settings visible."
        )
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._runtime_card)
        layout.addWidget(
            SectionCard(
                "Execution model",
                "Each run will become an immutable artifact with generated input, "
                "logs, command metadata, and output folders.",
            )
        )
        layout.addWidget(
            SectionCard(
                "Boundary",
                "This workspace deliberately does not launch gprMax yet. Stage 2 "
                "stops at project and settings persistence.",
            )
        )
        layout.addStretch(1)

    def set_runtime_label(self, runtime_label: str) -> None:
        label = self._runtime_card.findChild(QLabel, "SectionBody")
        if label is not None:
            label.setText(runtime_label)
