from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
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
        self._card_titles: dict[str, QLabel] = {}
        self._runtime_healthy = False
        self._diagnostics_count = 0

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")

        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._runtime_edit = QLineEdit()
        self._language_selector = QComboBox()
        self._advanced_mode_checkbox = QCheckBox()
        self._runtime_status_badge = QLabel()
        self._runtime_status_badge.setObjectName("StatusBadge")
        self._runtime_status_badge.setProperty("statusTone", "neutral")
        self._runtime_status_badge.setWordWrap(True)
        self._runtime_next_step_label = QLabel()
        self._runtime_next_step_label.setObjectName("StatusDetail")
        self._runtime_next_step_label.setWordWrap(True)
        self._runtime_summary_label = QLabel()
        self._runtime_summary_label.setObjectName("TechnicalDetails")
        self._runtime_summary_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._runtime_summary_label.setWordWrap(True)
        self._capabilities_label = QLabel()
        self._capabilities_label.setWordWrap(True)
        self._diagnostics_status_badge = QLabel()
        self._diagnostics_status_badge.setObjectName("StatusBadge")
        self._diagnostics_status_badge.setProperty("statusTone", "neutral")
        self._diagnostics_status_badge.setWordWrap(True)
        self._diagnostics_label = QLabel()
        self._diagnostics_label.setObjectName("TechnicalDetails")
        self._diagnostics_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._diagnostics_label.setWordWrap(True)
        self._runtime_details_button = self._build_details_button()
        self._diagnostics_details_button = self._build_details_button()
        self._save_button = QPushButton()
        self._save_button.setObjectName("PrimaryButton")

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(10)
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

        runtime_content = QWidget()
        runtime_layout = QVBoxLayout(runtime_content)
        runtime_layout.setContentsMargins(0, 0, 0, 0)
        runtime_layout.setSpacing(8)
        runtime_layout.addWidget(self._runtime_status_badge)
        runtime_layout.addWidget(self._runtime_next_step_label)
        runtime_layout.addWidget(self._capabilities_label)
        runtime_layout.addWidget(
            self._runtime_details_button,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        runtime_layout.addWidget(self._runtime_summary_label)

        diagnostics_content = QWidget()
        diagnostics_layout = QVBoxLayout(diagnostics_content)
        diagnostics_layout.setContentsMargins(0, 0, 0, 0)
        diagnostics_layout.setSpacing(8)
        diagnostics_layout.addWidget(self._diagnostics_status_badge)
        diagnostics_layout.addWidget(
            self._diagnostics_details_button,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        diagnostics_layout.addWidget(self._diagnostics_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._build_card("settings.preferences_section", form_widget))
        layout.addWidget(self._build_card("settings.runtime_section", runtime_content))
        layout.addWidget(
            self._build_card("settings.diagnostics_section", diagnostics_content)
        )
        layout.addLayout(actions)
        layout.addStretch(1)

        self._advanced_mode_checkbox.toggled.connect(self._update_runtime_field_state)
        self._runtime_details_button.toggled.connect(self._update_details_visibility)
        self._diagnostics_details_button.toggled.connect(
            self._update_details_visibility
        )
        self.retranslate_ui()
        self._update_runtime_field_state()
        self._update_details_visibility()

    def set_settings(
        self,
        settings: AppSettings,
        runtime_info: RuntimeInfo,
    ) -> None:
        self._populate_language_selector(settings.language)
        self._runtime_edit.setText(settings.gprmax_python_executable or "")
        self._advanced_mode_checkbox.setChecked(settings.advanced_mode)
        self._runtime_healthy = runtime_info.is_healthy
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
            "\n".join(
                self._format_capability(item)
                for item in runtime_info.capabilities
                if item.code != "gpu"
            )
        )
        diagnostics = runtime_info.diagnostics or [
            self._localization.text("settings.diagnostics_placeholder")
        ]
        self._diagnostics_count = len(runtime_info.diagnostics)
        self._diagnostics_label.setText(
            "\n".join(self._localization.translate_message(item) for item in diagnostics)
        )
        self._refresh_status_badges()
        self._update_runtime_field_state()
        self._update_details_visibility()

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
        for key, title in self._card_titles.items():
            title.setText(self._localization.text(key))
        self._refresh_status_badges()
        self._update_details_visibility()

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

    def _refresh_status_badges(self) -> None:
        runtime_key = (
            "settings.runtime_status.ready"
            if self._runtime_healthy
            else "settings.runtime_status.issue"
        )
        self._set_status_badge(
            self._runtime_status_badge,
            self._localization.text(runtime_key),
            "success" if self._runtime_healthy else "error",
        )
        self._runtime_next_step_label.setText(
            "" if self._runtime_healthy else self._localization.text("settings.runtime.next_step")
        )
        self._runtime_next_step_label.setVisible(not self._runtime_healthy)
        diagnostics_key = (
            "settings.diagnostics_status.clean"
            if self._diagnostics_count == 0
            else "settings.diagnostics_status.issues"
        )
        self._set_status_badge(
            self._diagnostics_status_badge,
            self._localization.text(diagnostics_key, count=self._diagnostics_count),
            "success" if self._diagnostics_count == 0 else "warning",
        )

    def _set_status_badge(self, badge: QLabel, text: str, tone: str) -> None:
        badge.setText(text)
        badge.setProperty("statusTone", tone)
        badge.style().unpolish(badge)
        badge.style().polish(badge)

    def _build_details_button(self) -> QPushButton:
        button = QPushButton()
        button.setCheckable(True)
        button.setProperty("buttonRole", "ghost")
        return button

    def _update_details_visibility(self) -> None:
        runtime_details_visible = self._runtime_details_button.isChecked()
        diagnostics_visible = self._diagnostics_details_button.isChecked()
        self._runtime_summary_label.setVisible(runtime_details_visible)
        self._diagnostics_label.setVisible(diagnostics_visible)
        self._runtime_details_button.setText(
            self._localization.text(
                "settings.action.hide_details"
                if runtime_details_visible
                else "settings.action.show_details"
            )
        )
        self._diagnostics_details_button.setText(
            self._localization.text(
                "settings.action.hide_details"
                if diagnostics_visible
                else "settings.action.show_details"
            )
        )

    def _build_card(self, title_key: str, content: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("ViewCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)
        title = QLabel()
        title.setObjectName("SectionTitle")
        self._card_titles[title_key] = title
        layout.addWidget(title)
        layout.addWidget(content)
        return card
