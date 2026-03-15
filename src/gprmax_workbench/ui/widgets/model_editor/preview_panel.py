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
from ....application.services.model_editor_service import ModelEditorService


class PreviewPanel(QWidget):
    preview_updated = Signal()

    def __init__(
        self,
        model_editor_service: ModelEditorService,
        input_preview_service: InputPreviewService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model_editor_service = model_editor_service
        self._input_preview_service = input_preview_service

        title = QLabel(
            "This preview is generated from the current in-memory model with the default run configuration. Runtime-specific flags remain on the Simulation screen."
        )
        title.setWordWrap(True)

        self._messages = QPlainTextEdit()
        self._messages.setReadOnly(True)
        self._messages.setPlaceholderText("Validation and preview messages")

        self._preview_text = QPlainTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setPlaceholderText("Generated gprMax input will appear here")

        rebuild_button = QPushButton("Rebuild Preview")
        rebuild_button.clicked.connect(self._rebuild_preview)
        export_button = QPushButton("Export Preview")
        export_button.clicked.connect(self._export_preview)

        buttons = QHBoxLayout()
        buttons.addWidget(rebuild_button)
        buttons.addWidget(export_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Messages"))
        layout.addWidget(self._messages, 1)
        layout.addWidget(QLabel("Input preview"))
        layout.addWidget(self._preview_text, 2)

    def clear(self) -> None:
        self._messages.clear()
        self._preview_text.clear()

    def _rebuild_preview(self) -> None:
        project = self._model_editor_service.current_project()
        if project is None:
            self.clear()
            return

        preview = self._input_preview_service.generate_preview(project)
        self._messages.setPlainText("\n".join(preview.messages))
        self._preview_text.setPlainText(preview.text)
        self.preview_updated.emit()

    def _export_preview(self) -> None:
        project = self._model_editor_service.current_project()
        if project is None:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Preview",
            str(project.root / "generated" / "model-editor-preview.in"),
            "gprMax input (*.in);;All files (*)",
        )
        if not filename:
            return

        destination = self._input_preview_service.export_preview(
            project,
            Path(filename),
        )
        self._messages.setPlainText(f"Preview exported to {destination}")
