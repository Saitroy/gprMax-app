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

from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.model_entities import EDITOR_SOURCE_AXES, EDITOR_SOURCE_KINDS
from ....domain.models import Project, SourceDefinition, Vector3
from ...layouts.flow_layout import FlowLayout
from ...splitters import configure_splitter
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_tags,
    tags_to_text,
)


class SourcesPanel(QWidget):
    model_changed = Signal()

    def __init__(
        self,
        localization: LocalizationService,
        model_editor_service: ModelEditorService,
        validation_service: ValidationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._model_editor_service = model_editor_service
        self._validation_service = validation_service
        self._loading = False

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._load_current_source)

        self._add_button = QPushButton()
        self._add_button.clicked.connect(self._add_source)
        self._duplicate_button = QPushButton()
        self._duplicate_button.clicked.connect(self._duplicate_source)
        self._delete_button = QPushButton()
        self._delete_button.clicked.connect(self._delete_source)

        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_title = QLabel()
        list_layout.addWidget(self._list_title)
        list_layout.addWidget(self._list, 1)
        buttons = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        buttons.addWidget(self._add_button)
        buttons.addWidget(self._duplicate_button)
        buttons.addWidget(self._delete_button)
        list_layout.addLayout(buttons)

        self._identifier_edit = QLineEdit()
        self._kind_combo = QComboBox()
        for kind in EDITOR_SOURCE_KINDS:
            self._kind_combo.addItem(kind, kind)
        self._axis_combo = QComboBox()
        for axis in EDITOR_SOURCE_AXES:
            self._axis_combo.addItem(axis, axis)
        self._waveform_combo = QComboBox()
        self._position_x = build_float_spinbox()
        self._position_y = build_float_spinbox()
        self._position_z = build_float_spinbox()
        self._delay = build_float_spinbox(
            minimum=0.0,
            maximum=1.0,
            decimals=12,
            step=1e-10,
        )
        self._resistance_edit = QLineEdit()
        self._resistance_edit.setPlaceholderText("")
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setFixedHeight(90)
        self._tags_edit = QLineEdit()
        self._status_label = build_status_label("")

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self._identifier_label = QLabel()
        self._kind_label = QLabel()
        self._axis_label = QLabel()
        self._waveform_label = QLabel()
        self._position_x_label = QLabel()
        self._position_y_label = QLabel()
        self._position_z_label = QLabel()
        self._delay_label = QLabel()
        self._resistance_label = QLabel()
        self._notes_label = QLabel()
        self._tags_label = QLabel()
        form.addRow(self._identifier_label, self._identifier_edit)
        form.addRow(self._kind_label, self._kind_combo)
        form.addRow(self._axis_label, self._axis_combo)
        form.addRow(self._waveform_label, self._waveform_combo)
        form.addRow(self._position_x_label, self._position_x)
        form.addRow(self._position_y_label, self._position_y)
        form.addRow(self._position_z_label, self._position_z)
        form.addRow(self._delay_label, self._delay)
        form.addRow(self._resistance_label, self._resistance_edit)
        form.addRow(self._notes_label, self._notes_edit)
        form.addRow(self._tags_label, self._tags_edit)
        detail_layout.addLayout(form)
        detail_layout.addWidget(self._status_label)
        detail_layout.addStretch(1)

        splitter = configure_splitter(QSplitter())
        splitter.addWidget(list_panel)
        splitter.addWidget(detail_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 640])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        for widget in (
            self._identifier_edit,
            self._resistance_edit,
            self._tags_edit,
        ):
            widget.textChanged.connect(self._apply_changes)
        self._kind_combo.currentIndexChanged.connect(self._apply_changes)
        self._axis_combo.currentIndexChanged.connect(self._apply_changes)
        self._waveform_combo.currentIndexChanged.connect(self._apply_changes)
        self._notes_edit.textChanged.connect(self._apply_changes)
        for widget in (
            self._position_x,
            self._position_y,
            self._position_z,
            self._delay,
        ):
            widget.valueChanged.connect(self._apply_changes)

        self.retranslate_ui()
        self.set_project(None)

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        self._list.clear()
        self.refresh_waveform_choices()
        if project is not None:
            for source in project.model.sources:
                self._list.addItem(self._item_text(source))
        self._loading = False

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._load_current_source(None)
        self._update_buttons()

    def refresh_waveform_choices(self) -> None:
        project = self._model_editor_service.current_project()
        current_value = self._waveform_combo.currentData()
        self._loading = True
        self._waveform_combo.clear()
        self._waveform_combo.addItem(
            self._localization.text("editor.sources.no_waveform"),
            "",
        )
        if project is not None:
            for waveform_id in self._model_editor_service.available_waveform_ids():
                self._waveform_combo.addItem(waveform_id, waveform_id)
        index = self._waveform_combo.findData(current_value)
        if index >= 0:
            self._waveform_combo.setCurrentIndex(index)
        self._loading = False

    def refresh_validation(self) -> None:
        row = self._list.currentRow()
        prefixes = ["model.sources"]
        if row >= 0:
            prefixes.insert(0, f"model.sources[{row}]")
        self._status_label.setText(
            join_messages(
                self._validation_service.messages_for_prefixes(*prefixes),
                self._localization.text("editor.sources.valid"),
            )
        )

    def _load_current_source(self, row: int | None) -> None:
        project = self._model_editor_service.current_project()
        self._loading = True
        enabled = (
            project is not None
            and row is not None
            and 0 <= row < len(project.model.sources)
        )
        for widget in (
            self._identifier_edit,
            self._kind_combo,
            self._axis_combo,
            self._waveform_combo,
            self._position_x,
            self._position_y,
            self._position_z,
            self._delay,
            self._resistance_edit,
            self._notes_edit,
            self._tags_edit,
        ):
            widget.setEnabled(enabled)

        if not enabled or project is None:
            self._identifier_edit.clear()
            self._kind_combo.setCurrentIndex(0)
            self._axis_combo.setCurrentIndex(0)
            self._waveform_combo.setCurrentIndex(0)
            self._position_x.setValue(0.0)
            self._position_y.setValue(0.0)
            self._position_z.setValue(0.0)
            self._delay.setValue(0.0)
            self._resistance_edit.clear()
            self._notes_edit.clear()
            self._tags_edit.clear()
            self._loading = False
            self.refresh_validation()
            self._update_buttons()
            return

        source = project.model.sources[row]
        self._identifier_edit.setText(source.identifier)
        self._kind_combo.setCurrentText(source.kind)
        self._axis_combo.setCurrentText(source.axis)
        waveform_index = self._waveform_combo.findData(source.waveform_id)
        self._waveform_combo.setCurrentIndex(waveform_index if waveform_index >= 0 else 0)
        self._position_x.setValue(source.position_m.x)
        self._position_y.setValue(source.position_m.y)
        self._position_z.setValue(source.position_m.z)
        self._delay.setValue(source.delay_s)
        self._resistance_edit.setText(
            "" if source.resistance_ohms is None else str(source.resistance_ohms)
        )
        self._notes_edit.setPlainText(source.notes)
        self._tags_edit.setText(tags_to_text(source.tags))
        self._loading = False
        self._update_resistance_enabled()
        self.refresh_validation()
        self._update_buttons()

    def _apply_changes(self) -> None:
        row = self._list.currentRow()
        project = self._model_editor_service.current_project()
        if self._loading or project is None or not (0 <= row < len(project.model.sources)):
            return

        resistance_text = self._resistance_edit.text().strip()
        try:
            resistance = float(resistance_text) if resistance_text else None
        except ValueError:
            return
        kind = self._kind_combo.currentText()
        if kind != "voltage_source":
            resistance = None

        source = SourceDefinition(
            identifier=self._identifier_edit.text(),
            kind=kind,
            axis=self._axis_combo.currentText(),
            position_m=Vector3(
                x=self._position_x.value(),
                y=self._position_y.value(),
                z=self._position_z.value(),
            ),
            waveform_id=str(self._waveform_combo.currentData() or ""),
            delay_s=self._delay.value(),
            resistance_ohms=resistance,
            notes=self._notes_edit.toPlainText(),
            tags=parse_tags(self._tags_edit.text()),
        )
        self._model_editor_service.update_source(row, source)
        self._list.item(row).setText(self._item_text(source))
        self._update_resistance_enabled()
        self.refresh_validation()
        self.model_changed.emit()

    def _add_source(self) -> None:
        index = self._model_editor_service.add_source()
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _duplicate_source(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        index = self._model_editor_service.duplicate_source(row)
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _delete_source(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        next_index = self._model_editor_service.delete_source(row)
        self.set_project(self._model_editor_service.current_project())
        if next_index is not None:
            self._list.setCurrentRow(next_index)
        self.model_changed.emit()

    def _item_text(self, source: SourceDefinition) -> str:
        name = source.identifier or source.kind
        return (
            f"{name} | {source.kind} | "
            f"{source.waveform_id or self._localization.text('editor.sources.no_waveform_item')}"
        )

    def _update_buttons(self) -> None:
        enabled = self._list.currentRow() >= 0
        self._duplicate_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)

    def _update_resistance_enabled(self) -> None:
        self._resistance_edit.setEnabled(
            self._kind_combo.currentText() == "voltage_source"
            and self._list.currentRow() >= 0
        )

    def retranslate_ui(self) -> None:
        self._list_title.setText(self._localization.text("editor.sources.list_title"))
        self._add_button.setText(self._localization.text("common.add"))
        self._duplicate_button.setText(self._localization.text("common.duplicate"))
        self._delete_button.setText(self._localization.text("common.delete"))
        self._identifier_label.setText(self._localization.text("editor.sources.identifier"))
        self._kind_label.setText(self._localization.text("editor.sources.kind"))
        self._axis_label.setText(self._localization.text("editor.sources.axis"))
        self._waveform_label.setText(self._localization.text("editor.sources.waveform"))
        self._position_x_label.setText(self._localization.text("editor.sources.position_x"))
        self._position_y_label.setText(self._localization.text("editor.sources.position_y"))
        self._position_z_label.setText(self._localization.text("editor.sources.position_z"))
        self._delay_label.setText(self._localization.text("editor.sources.delay"))
        self._resistance_label.setText(self._localization.text("editor.sources.resistance"))
        self._notes_label.setText(self._localization.text("editor.sources.notes"))
        self._tags_label.setText(self._localization.text("editor.sources.tags"))
        self._resistance_edit.setPlaceholderText(
            self._localization.text("editor.sources.resistance_placeholder")
        )
        self.refresh_waveform_choices()
        if self._list.currentRow() < 0:
            self._status_label.setText(self._localization.text("editor.sources.select"))
        else:
            self.refresh_validation()
