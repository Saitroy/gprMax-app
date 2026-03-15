from __future__ import annotations

from typing import Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...infrastructure.settings import AppSettings


class SettingsView(QWidget):
    save_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        title = QLabel("Settings")
        title.setObjectName("ViewTitle")

        subtitle = QLabel(
            "Persist application-level preferences such as advanced mode and the "
            "Python executable used to launch gprMax."
        )
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        self._runtime_edit = QLineEdit()
        self._advanced_mode_checkbox = QCheckBox("Enable advanced mode")
        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("gprMax Python executable", self._runtime_edit)
        form.addRow("", self._advanced_mode_checkbox)

        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addWidget(self._summary_label)
        layout.addStretch(1)

    def set_settings(self, settings: AppSettings, summary: Mapping[str, str]) -> None:
        self._runtime_edit.setText(settings.gprmax_python_executable or "")
        self._advanced_mode_checkbox.setChecked(settings.advanced_mode)
        self._summary_label.setText(
            "\n".join(f"{key}: {value}" for key, value in summary.items())
        )

    def runtime_executable(self) -> str:
        return self._runtime_edit.text().strip()

    def advanced_mode_enabled(self) -> bool:
        return self._advanced_mode_checkbox.isChecked()
