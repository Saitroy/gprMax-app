from __future__ import annotations

from typing import Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...application.services.localization_service import LocalizationService
from ...infrastructure.settings import AppSettings


class SettingsView(QWidget):
    save_requested = Signal()

    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")

        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._runtime_edit = QLineEdit()
        self._language_selector = QComboBox()
        self._advanced_mode_checkbox = QCheckBox()
        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)
        self._save_button = QPushButton()
        self._save_button.setObjectName("PrimaryButton")

        form = QFormLayout()
        self._language_label = QLabel()
        self._runtime_label = QLabel()
        form.addRow(self._language_label, self._language_selector)
        form.addRow(self._runtime_label, self._runtime_edit)
        form.addRow("", self._advanced_mode_checkbox)

        self._save_button.clicked.connect(self.save_requested.emit)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addWidget(self._save_button, 0)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addLayout(actions)
        layout.addLayout(form)
        layout.addWidget(self._summary_label)
        layout.addStretch(1)

        self.retranslate_ui()

    def set_settings(self, settings: AppSettings, summary: Mapping[str, str]) -> None:
        self._populate_language_selector(settings.language)
        self._runtime_edit.setText(settings.gprmax_python_executable or "")
        self._advanced_mode_checkbox.setChecked(settings.advanced_mode)
        self._summary_label.setText(
            "\n".join(
                f"{self._localization.text(f'settings.summary.{key}')}:" f" {self._format_summary_value(key, value)}"
                for key, value in summary.items()
            )
        )

    def runtime_executable(self) -> str:
        return self._runtime_edit.text().strip()

    def advanced_mode_enabled(self) -> bool:
        return self._advanced_mode_checkbox.isChecked()

    def selected_language(self) -> str:
        data = self._language_selector.currentData()
        return data if isinstance(data, str) else "ru"

    def retranslate_ui(self) -> None:
        self._title.setText(self._localization.text("settings.title"))
        self._subtitle.setText(self._localization.text("settings.subtitle"))
        self._language_label.setText(self._localization.text("language.label"))
        self._runtime_label.setText(
            self._localization.text("settings.runtime_executable")
        )
        self._advanced_mode_checkbox.setText(
            self._localization.text("settings.advanced_mode")
        )
        self._save_button.setText(self._localization.text("settings.save"))
        self._populate_language_selector(self.selected_language())

    def _populate_language_selector(self, selected_language: str) -> None:
        current = selected_language or self.selected_language()
        self._language_selector.blockSignals(True)
        self._language_selector.clear()
        for option in self._localization.language_options():
            self._language_selector.addItem(option.label, option.code)
        index = self._language_selector.findData(current)
        if index >= 0:
            self._language_selector.setCurrentIndex(index)
        self._language_selector.blockSignals(False)

    def _format_summary_value(self, key: str, value: str) -> str:
        if key == "advanced_mode":
            return self._localization.bool_text(value == "true")
        if key == "interface_language":
            return self._localization.text(f"language.option.{value}")
        return value
