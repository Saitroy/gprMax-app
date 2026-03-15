from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ....application.services.input_preview_service import InputPreviewService
from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService


class PreviewPanel(QWidget):
    preview_updated = Signal()

    def __init__(
        self,
        localization: LocalizationService,
        model_editor_service: ModelEditorService,
        input_preview_service: InputPreviewService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._model_editor_service = model_editor_service
        self._input_preview_service = input_preview_service

        self._title = QLabel()
        self._title.setWordWrap(True)

        self._messages = QPlainTextEdit()
        self._messages.setReadOnly(True)
        self._messages.setPlaceholderText("")

        self._preview_text = QPlainTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setPlaceholderText("")

        self._rebuild_button = QPushButton()
        self._rebuild_button.clicked.connect(self._rebuild_preview)
        self._export_button = QPushButton()
        self._export_button.clicked.connect(self._export_preview)

        buttons = QHBoxLayout()
        buttons.addWidget(self._rebuild_button)
        buttons.addWidget(self._export_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._title)
        layout.addLayout(buttons)
        self._messages_label = QLabel()
        layout.addWidget(self._messages_label)
        layout.addWidget(self._messages, 1)
        self._input_label = QLabel()
        layout.addWidget(self._input_label)
        layout.addWidget(self._preview_text, 2)
        self.retranslate_ui()

    def clear(self) -> None:
        self._messages.clear()
        self._preview_text.clear()

    def _rebuild_preview(self) -> None:
        project = self._model_editor_service.current_project()
        if project is None:
            self.clear()
            return

        preview = self._input_preview_service.generate_preview(project)
        self._messages.setPlainText(
            "\n".join(
                self._localization.translate_message(message)
                for message in preview.messages
            )
        )
        self._preview_text.setPlainText(preview.text)
        self.preview_updated.emit()

    def _export_preview(self) -> None:
        project = self._model_editor_service.current_project()
        if project is None:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            self._localization.text("editor.preview.export_dialog"),
            str(project.root / "generated" / "model-editor-preview.in"),
            self._localization.text("dialog.export_preview_filter"),
        )
        if not filename:
            return

        destination = self._input_preview_service.export_preview(
            project,
            Path(filename),
        )
        self._messages.setPlainText(
            self._localization.text(
                "editor.preview.exported",
                destination=destination,
            )
        )

    def retranslate_ui(self) -> None:
        self._title.setText(self._localization.text("editor.preview.title"))
        self._messages.setPlaceholderText(
            self._localization.text("editor.preview.messages_placeholder")
        )
        self._preview_text.setPlaceholderText(
            self._localization.text("editor.preview.text_placeholder")
        )
        self._rebuild_button.setText(self._localization.text("editor.preview.rebuild"))
        self._export_button.setText(self._localization.text("editor.preview.export"))
        self._messages_label.setText(self._localization.text("editor.preview.messages"))
        self._input_label.setText(self._localization.text("editor.preview.input"))
