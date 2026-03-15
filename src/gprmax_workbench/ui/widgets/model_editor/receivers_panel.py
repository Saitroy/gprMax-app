from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
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
from ....domain.models import Project, ReceiverDefinition, Vector3
from ...layouts.flow_layout import FlowLayout
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_csv_values,
    parse_tags,
    tags_to_text,
)


class ReceiversPanel(QWidget):
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
        self._list.currentRowChanged.connect(self._load_current_receiver)

        self._add_button = QPushButton()
        self._add_button.clicked.connect(self._add_receiver)
        self._duplicate_button = QPushButton()
        self._duplicate_button.clicked.connect(self._duplicate_receiver)
        self._delete_button = QPushButton()
        self._delete_button.clicked.connect(self._delete_receiver)

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
        self._position_x = build_float_spinbox()
        self._position_y = build_float_spinbox()
        self._position_z = build_float_spinbox()
        self._outputs_edit = QLineEdit()
        self._outputs_edit.setPlaceholderText("")
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setFixedHeight(90)
        self._tags_edit = QLineEdit()
        self._status_label = build_status_label("")

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self._identifier_label = QLabel()
        self._position_x_label = QLabel()
        self._position_y_label = QLabel()
        self._position_z_label = QLabel()
        self._outputs_label = QLabel()
        self._notes_label = QLabel()
        self._tags_label = QLabel()
        form.addRow(self._identifier_label, self._identifier_edit)
        form.addRow(self._position_x_label, self._position_x)
        form.addRow(self._position_y_label, self._position_y)
        form.addRow(self._position_z_label, self._position_z)
        form.addRow(self._outputs_label, self._outputs_edit)
        form.addRow(self._notes_label, self._notes_edit)
        form.addRow(self._tags_label, self._tags_edit)
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

        for widget in (
            self._identifier_edit,
            self._outputs_edit,
            self._tags_edit,
        ):
            widget.textChanged.connect(self._apply_changes)
        self._notes_edit.textChanged.connect(self._apply_changes)
        for widget in (
            self._position_x,
            self._position_y,
            self._position_z,
        ):
            widget.valueChanged.connect(self._apply_changes)

        self.retranslate_ui()
        self.set_project(None)

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        self._list.clear()
        if project is not None:
            for receiver in project.model.receivers:
                self._list.addItem(self._item_text(receiver))
        self._loading = False

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._load_current_receiver(None)
        self._update_buttons()

    def refresh_validation(self) -> None:
        row = self._list.currentRow()
        prefixes = ["model.receivers"]
        if row >= 0:
            prefixes.insert(0, f"model.receivers[{row}]")
        self._status_label.setText(
            join_messages(
                self._validation_service.messages_for_prefixes(*prefixes),
                self._localization.text("editor.receivers.valid"),
            )
        )

    def _load_current_receiver(self, row: int | None) -> None:
        project = self._model_editor_service.current_project()
        self._loading = True
        enabled = (
            project is not None
            and row is not None
            and 0 <= row < len(project.model.receivers)
        )
        for widget in (
            self._identifier_edit,
            self._position_x,
            self._position_y,
            self._position_z,
            self._outputs_edit,
            self._notes_edit,
            self._tags_edit,
        ):
            widget.setEnabled(enabled)

        if not enabled or project is None:
            self._identifier_edit.clear()
            self._position_x.setValue(0.0)
            self._position_y.setValue(0.0)
            self._position_z.setValue(0.0)
            self._outputs_edit.clear()
            self._notes_edit.clear()
            self._tags_edit.clear()
            self._loading = False
            self.refresh_validation()
            self._update_buttons()
            return

        receiver = project.model.receivers[row]
        self._identifier_edit.setText(receiver.identifier)
        self._position_x.setValue(receiver.position_m.x)
        self._position_y.setValue(receiver.position_m.y)
        self._position_z.setValue(receiver.position_m.z)
        self._outputs_edit.setText(", ".join(receiver.outputs))
        self._notes_edit.setPlainText(receiver.notes)
        self._tags_edit.setText(tags_to_text(receiver.tags))
        self._loading = False
        self.refresh_validation()
        self._update_buttons()

    def _apply_changes(self) -> None:
        row = self._list.currentRow()
        project = self._model_editor_service.current_project()
        if self._loading or project is None or not (0 <= row < len(project.model.receivers)):
            return

        receiver = ReceiverDefinition(
            identifier=self._identifier_edit.text(),
            position_m=Vector3(
                x=self._position_x.value(),
                y=self._position_y.value(),
                z=self._position_z.value(),
            ),
            outputs=parse_csv_values(self._outputs_edit.text()),
            notes=self._notes_edit.toPlainText(),
            tags=parse_tags(self._tags_edit.text()),
        )
        self._model_editor_service.update_receiver(row, receiver)
        self._list.item(row).setText(self._item_text(receiver))
        self.refresh_validation()
        self.model_changed.emit()

    def _add_receiver(self) -> None:
        index = self._model_editor_service.add_receiver()
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _duplicate_receiver(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        index = self._model_editor_service.duplicate_receiver(row)
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _delete_receiver(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        next_index = self._model_editor_service.delete_receiver(row)
        self.set_project(self._model_editor_service.current_project())
        if next_index is not None:
            self._list.setCurrentRow(next_index)
        self.model_changed.emit()

    def _item_text(self, receiver: ReceiverDefinition) -> str:
        name = receiver.identifier or self._localization.text("editor.receivers.default_name")
        return (
            f"{name} | "
            f"({receiver.position_m.x:.3g}, {receiver.position_m.y:.3g}, {receiver.position_m.z:.3g})"
        )

    def _update_buttons(self) -> None:
        enabled = self._list.currentRow() >= 0
        self._duplicate_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)

    def retranslate_ui(self) -> None:
        self._list_title.setText(self._localization.text("editor.receivers.list_title"))
        self._add_button.setText(self._localization.text("common.add"))
        self._duplicate_button.setText(self._localization.text("common.duplicate"))
        self._delete_button.setText(self._localization.text("common.delete"))
        self._identifier_label.setText(self._localization.text("editor.receivers.identifier"))
        self._position_x_label.setText(self._localization.text("editor.receivers.position_x"))
        self._position_y_label.setText(self._localization.text("editor.receivers.position_y"))
        self._position_z_label.setText(self._localization.text("editor.receivers.position_z"))
        self._outputs_label.setText(self._localization.text("editor.receivers.outputs"))
        self._notes_label.setText(self._localization.text("editor.receivers.notes"))
        self._tags_label.setText(self._localization.text("editor.receivers.tags"))
        self._outputs_edit.setPlaceholderText(
            self._localization.text("editor.receivers.outputs_placeholder")
        )
        if self._list.currentRow() < 0:
            self._status_label.setText(self._localization.text("editor.receivers.select"))
        else:
            self.refresh_validation()
