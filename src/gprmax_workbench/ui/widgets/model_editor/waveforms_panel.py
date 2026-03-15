from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.model_entities import EDITOR_WAVEFORM_KINDS
from ....domain.models import Project, WaveformDefinition
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_tags,
    tags_to_text,
)


class WaveformsPanel(QWidget):
    model_changed = Signal()

    def __init__(
        self,
        model_editor_service: ModelEditorService,
        validation_service: ValidationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model_editor_service = model_editor_service
        self._validation_service = validation_service
        self._loading = False

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._load_current_waveform)

        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_waveform)
        duplicate_button = QPushButton("Duplicate")
        duplicate_button.clicked.connect(self._duplicate_waveform)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._delete_waveform)
        self._duplicate_button = duplicate_button
        self._delete_button = delete_button

        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(QLabel("Waveforms"))
        list_layout.addWidget(self._list, 1)
        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(duplicate_button)
        buttons.addWidget(delete_button)
        buttons.addStretch(1)
        list_layout.addLayout(buttons)

        self._identifier_edit = QLineEdit()
        self._kind_combo = QComboBox()
        for kind in EDITOR_WAVEFORM_KINDS:
            self._kind_combo.addItem(kind, kind)
        self._amplitude = build_float_spinbox(minimum=0.0)
        self._center_frequency = build_float_spinbox(
            minimum=0.0,
            maximum=1e15,
            step=1e7,
        )
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setFixedHeight(90)
        self._tags_edit = QLineEdit()
        self._status_label = build_status_label("Select a waveform to edit it.")

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        form.addRow("Identifier", self._identifier_edit)
        form.addRow("Kind", self._kind_combo)
        form.addRow("Amplitude", self._amplitude)
        form.addRow("Center frequency (Hz)", self._center_frequency)
        form.addRow("Notes", self._notes_edit)
        form.addRow("Tags", self._tags_edit)
        detail_layout.addLayout(form)
        detail_layout.addWidget(self._status_label)
        detail_layout.addStretch(1)

        splitter = QSplitter()
        splitter.addWidget(list_panel)
        splitter.addWidget(detail_panel)
        splitter.setSizes([320, 640])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self._identifier_edit.textChanged.connect(self._apply_changes)
        self._kind_combo.currentIndexChanged.connect(self._apply_changes)
        self._amplitude.valueChanged.connect(self._apply_changes)
        self._center_frequency.valueChanged.connect(self._apply_changes)
        self._notes_edit.textChanged.connect(self._apply_changes)
        self._tags_edit.textChanged.connect(self._apply_changes)

        self.set_project(None)

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        self._list.clear()
        if project is not None:
            for waveform in project.model.waveforms:
                self._list.addItem(self._item_text(waveform))
        self._loading = False

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._load_current_waveform(None)
        self._update_buttons()

    def refresh_validation(self) -> None:
        row = self._list.currentRow()
        prefixes = ["model.waveforms"]
        if row >= 0:
            prefixes.insert(0, f"model.waveforms[{row}]")
        self._status_label.setText(
            join_messages(
                self._validation_service.messages_for_prefixes(*prefixes),
                "No waveform-specific validation issues.",
            )
        )

    def _load_current_waveform(self, row: int | None) -> None:
        project = self._model_editor_service.current_project()
        self._loading = True
        enabled = (
            project is not None
            and row is not None
            and 0 <= row < len(project.model.waveforms)
        )
        for widget in (
            self._identifier_edit,
            self._kind_combo,
            self._amplitude,
            self._center_frequency,
            self._notes_edit,
            self._tags_edit,
        ):
            widget.setEnabled(enabled)

        if not enabled or project is None:
            self._identifier_edit.clear()
            self._kind_combo.setCurrentIndex(0)
            self._amplitude.setValue(1.0)
            self._center_frequency.setValue(1e9)
            self._notes_edit.clear()
            self._tags_edit.clear()
            self._loading = False
            self.refresh_validation()
            self._update_buttons()
            return

        waveform = project.model.waveforms[row]
        self._identifier_edit.setText(waveform.identifier)
        self._kind_combo.setCurrentText(waveform.kind)
        self._amplitude.setValue(waveform.amplitude)
        self._center_frequency.setValue(waveform.center_frequency_hz)
        self._notes_edit.setPlainText(waveform.notes)
        self._tags_edit.setText(tags_to_text(waveform.tags))
        self._loading = False
        self.refresh_validation()
        self._update_buttons()

    def _apply_changes(self) -> None:
        row = self._list.currentRow()
        project = self._model_editor_service.current_project()
        if self._loading or project is None or not (0 <= row < len(project.model.waveforms)):
            return

        waveform = WaveformDefinition(
            identifier=self._identifier_edit.text(),
            kind=self._kind_combo.currentText(),
            amplitude=self._amplitude.value(),
            center_frequency_hz=self._center_frequency.value(),
            notes=self._notes_edit.toPlainText(),
            tags=parse_tags(self._tags_edit.text()),
        )
        self._model_editor_service.update_waveform(row, waveform)
        self._list.item(row).setText(self._item_text(waveform))
        self.refresh_validation()
        self.model_changed.emit()

    def _add_waveform(self) -> None:
        index = self._model_editor_service.add_waveform()
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _duplicate_waveform(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        index = self._model_editor_service.duplicate_waveform(row)
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _delete_waveform(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        next_index = self._model_editor_service.delete_waveform(row)
        self.set_project(self._model_editor_service.current_project())
        if next_index is not None:
            self._list.setCurrentRow(next_index)
        self.model_changed.emit()

    def _item_text(self, waveform: WaveformDefinition) -> str:
        return f"{waveform.identifier or '<unnamed>'} | {waveform.kind}"

    def _update_buttons(self) -> None:
        enabled = self._list.currentRow() >= 0
        self._duplicate_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)
