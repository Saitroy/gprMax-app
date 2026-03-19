from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout

from ..views.settings_view import SettingsView


class SettingsDialog(QDialog):
    def __init__(self, settings_view: SettingsView, parent=None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self.setMinimumSize(760, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(settings_view)

    def retranslate_ui(self, title: str) -> None:
        self.setWindowTitle(title)
