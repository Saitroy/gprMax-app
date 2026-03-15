from __future__ import annotations

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
from ...domain.capability_status import CapabilityStatus
from ...domain.runtime_info import RuntimeInfo
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
        self._section_titles: list[QLabel] = []

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")

        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._runtime_edit = QLineEdit()
        self._language_selector = QComboBox()
        self._advanced_mode_checkbox = QCheckBox()
        self._runtime_summary_label = QLabel()
        self._runtime_summary_label.setWordWrap(True)
        self._capabilities_label = QLabel()
        self._capabilities_label.setWordWrap(True)
        self._diagnostics_label = QLabel()
        self._diagnostics_label.setWordWrap(True)
        self._save_button = QPushButton()
        self._save_button.setObjectName("PrimaryButton")

        form = QFormLayout()
        self._language_label = QLabel()
        self._runtime_label = QLabel()
        self._runtime_label.setWordWrap(True)
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
        layout.addWidget(self._build_section("settings.runtime_section", self._runtime_summary_label))
        layout.addWidget(self._build_section("settings.capabilities_section", self._capabilities_label))
        layout.addWidget(self._build_section("settings.diagnostics_section", self._diagnostics_label))
        layout.addStretch(1)

        self._advanced_mode_checkbox.toggled.connect(self._update_runtime_field_state)
        self.retranslate_ui()

    def set_settings(
        self,
        settings: AppSettings,
        runtime_info: RuntimeInfo,
    ) -> None:
        self._populate_language_selector(settings.language)
        self._runtime_edit.setText(settings.gprmax_python_executable or "")
        self._advanced_mode_checkbox.setChecked(settings.advanced_mode)
        self._runtime_summary_label.setText(
            "\n".join(
                [
                    f"{self._localization.text('settings.runtime_mode')}: {self._localize_runtime_mode(runtime_info.engine.mode.value)}",
                    f"{self._localization.text('settings.install_root')}: {runtime_info.engine.installation_root or self._localization.text('common.not_set')}",
                    f"{self._localization.text('settings.engine_root')}: {runtime_info.engine.engine_root or self._localization.text('common.not_set')}",
                    f"{self._localization.text('settings.python_executable')}: {runtime_info.engine.python_executable}",
                    f"{self._localization.text('settings.app_version')}: {runtime_info.app_version}",
                    f"{self._localization.text('settings.engine_version')}: {runtime_info.bundled_engine_version or self._localization.text('common.not_set')}",
                    f"{self._localization.text('settings.gprmax_version_label')}: {runtime_info.gprmax_version or self._localization.text('common.not_set')}",
                    f"{self._localization.text('settings.summary.settings_file')}: {runtime_info.settings_path}",
                    f"{self._localization.text('settings.summary.logs_directory')}: {runtime_info.logs_directory}",
                    f"{self._localization.text('settings.cache_directory')}: {runtime_info.cache_directory}",
                    f"{self._localization.text('settings.temp_directory')}: {runtime_info.temp_directory}",
                ]
            )
        )
        self._capabilities_label.setText(
            "\n".join(self._format_capability(item) for item in runtime_info.capabilities)
        )
        diagnostics = runtime_info.diagnostics or [
            self._localization.text("settings.diagnostics_placeholder")
        ]
        self._diagnostics_label.setText(
            "\n".join(self._localization.translate_message(item) for item in diagnostics)
        )
        self._update_runtime_field_state()

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
            self._localization.text("settings.external_runtime_executable")
        )
        self._advanced_mode_checkbox.setText(
            self._localization.text("settings.advanced_mode")
        )
        self._save_button.setText(self._localization.text("settings.save"))
        self._populate_language_selector(self.selected_language())
        self._runtime_edit.setPlaceholderText(
            self._localization.text("settings.external_runtime_placeholder")
        )
        for title in self._section_titles:
            key = title.property("title_key")
            if isinstance(key, str):
                title.setText(self._localization.text(key))

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

    def _format_capability(self, capability: CapabilityStatus) -> str:
        return (
            f"{self._localization.text(f'settings.capability.{capability.code}')}: "
            f"{self._localization.text(f'settings.capability_status.{capability.level.value}')}"
        )

    def _localize_runtime_mode(self, mode: str) -> str:
        return self._localization.text(f"settings.runtime_mode.{mode}")

    def _update_runtime_field_state(self) -> None:
        enabled = self._advanced_mode_checkbox.isChecked()
        self._runtime_edit.setEnabled(enabled)

    def _build_section(self, title_key: str, content: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title = QLabel(self._localization.text(title_key))
        title.setObjectName("SectionTitle")
        title.setProperty("title_key", title_key)
        self._section_titles.append(title)
        layout.addWidget(title)
        layout.addWidget(content)
        return container
