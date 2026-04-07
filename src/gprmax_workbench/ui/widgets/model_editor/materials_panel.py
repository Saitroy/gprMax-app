from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
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
from ....domain.models import MaterialDefinition, Project
from ...layouts.flow_layout import FlowLayout
from ...splitters import configure_splitter
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_tags,
    tags_to_text,
)


class MaterialsPanel(QWidget):
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
        self._list.currentRowChanged.connect(self._load_current_material)

        self._add_button = QPushButton()
        self._add_button.clicked.connect(self._add_material)
        self._duplicate_button = QPushButton()
        self._duplicate_button.clicked.connect(self._duplicate_material)
        self._delete_button = QPushButton()
        self._delete_button.clicked.connect(self._delete_material)

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
        self._relative_permittivity = build_float_spinbox(minimum=0.0)
        self._conductivity = build_float_spinbox(minimum=0.0)
        self._relative_permeability = build_float_spinbox(minimum=0.0)
        self._magnetic_loss = build_float_spinbox(minimum=0.0)
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setFixedHeight(90)
        self._tags_edit = QLineEdit()
        self._status_label = build_status_label("")

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self._identifier_label = QLabel()
        self._relative_permittivity_label = QLabel()
        self._conductivity_label = QLabel()
        self._relative_permeability_label = QLabel()
        self._magnetic_loss_label = QLabel()
        self._notes_label = QLabel()
        self._tags_label = QLabel()
        form.addRow(self._identifier_label, self._identifier_edit)
        form.addRow(self._relative_permittivity_label, self._relative_permittivity)
        form.addRow(self._conductivity_label, self._conductivity)
        form.addRow(self._relative_permeability_label, self._relative_permeability)
        form.addRow(self._magnetic_loss_label, self._magnetic_loss)
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
            self._tags_edit,
        ):
            widget.textChanged.connect(self._apply_changes)
        self._notes_edit.textChanged.connect(self._apply_changes)
        for widget in (
            self._relative_permittivity,
            self._conductivity,
            self._relative_permeability,
            self._magnetic_loss,
        ):
            widget.valueChanged.connect(self._apply_changes)

        self.retranslate_ui()
        self.set_project(None)

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        self._list.clear()
        if project is not None:
            for material in project.model.materials:
                self._list.addItem(self._item_text(material))
        self._loading = False

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._load_current_material(None)
        self._update_buttons()

    def refresh_validation(self) -> None:
        row = self._list.currentRow()
        prefixes = ["model.materials"]
        if row >= 0:
            prefixes.insert(0, f"model.materials[{row}]")
        self._status_label.setText(
            join_messages(
                self._validation_service.messages_for_prefixes(*prefixes),
                self._localization.text("editor.materials.valid"),
            )
        )

    def _load_current_material(self, row: int | None) -> None:
        project = self._model_editor_service.current_project()
        self._loading = True
        enabled = (
            project is not None
            and row is not None
            and 0 <= row < len(project.model.materials)
        )
        for widget in (
            self._identifier_edit,
            self._relative_permittivity,
            self._conductivity,
            self._relative_permeability,
            self._magnetic_loss,
            self._notes_edit,
            self._tags_edit,
        ):
            widget.setEnabled(enabled)

        if not enabled or project is None:
            self._identifier_edit.clear()
            self._relative_permittivity.setValue(0.0)
            self._conductivity.setValue(0.0)
            self._relative_permeability.setValue(1.0)
            self._magnetic_loss.setValue(0.0)
            self._notes_edit.clear()
            self._tags_edit.clear()
            self._loading = False
            self.refresh_validation()
            self._update_buttons()
            return

        material = project.model.materials[row]
        self._identifier_edit.setText(material.identifier)
        self._relative_permittivity.setValue(material.relative_permittivity)
        self._conductivity.setValue(material.conductivity)
        self._relative_permeability.setValue(material.relative_permeability)
        self._magnetic_loss.setValue(material.magnetic_loss)
        self._notes_edit.setPlainText(material.notes)
        self._tags_edit.setText(tags_to_text(material.tags))
        self._loading = False
        self.refresh_validation()
        self._update_buttons()

    def _apply_changes(self) -> None:
        row = self._list.currentRow()
        project = self._model_editor_service.current_project()
        if self._loading or project is None or not (0 <= row < len(project.model.materials)):
            return

        material = MaterialDefinition(
            identifier=self._identifier_edit.text(),
            relative_permittivity=self._relative_permittivity.value(),
            conductivity=self._conductivity.value(),
            relative_permeability=self._relative_permeability.value(),
            magnetic_loss=self._magnetic_loss.value(),
            notes=self._notes_edit.toPlainText(),
            tags=parse_tags(self._tags_edit.text()),
        )
        self._model_editor_service.update_material(row, material)
        self._list.item(row).setText(self._item_text(material))
        self.refresh_validation()
        self.model_changed.emit()

    def _add_material(self) -> None:
        index = self._model_editor_service.add_material()
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _duplicate_material(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        index = self._model_editor_service.duplicate_material(row)
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _delete_material(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        next_index = self._model_editor_service.delete_material(row)
        self.set_project(self._model_editor_service.current_project())
        if next_index is not None:
            self._list.setCurrentRow(next_index)
        self.model_changed.emit()

    def _item_text(self, material: MaterialDefinition) -> str:
        return (
            f"{material.identifier or self._localization.text('editor.materials.unnamed')} "
            f"| er={material.relative_permittivity:.3g}"
        )

    def _update_buttons(self) -> None:
        enabled = self._list.currentRow() >= 0
        self._duplicate_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)

    def retranslate_ui(self) -> None:
        self._list_title.setText(self._localization.text("editor.materials.list_title"))
        self._add_button.setText(self._localization.text("common.add"))
        self._duplicate_button.setText(self._localization.text("common.duplicate"))
        self._delete_button.setText(self._localization.text("common.delete"))
        self._identifier_label.setText(self._localization.text("editor.materials.identifier"))
        self._relative_permittivity_label.setText(
            self._localization.text("editor.materials.relative_permittivity")
        )
        self._conductivity_label.setText(
            self._localization.text("editor.materials.conductivity")
        )
        self._relative_permeability_label.setText(
            self._localization.text("editor.materials.relative_permeability")
        )
        self._magnetic_loss_label.setText(
            self._localization.text("editor.materials.magnetic_loss")
        )
        self._notes_label.setText(self._localization.text("editor.materials.notes"))
        self._tags_label.setText(self._localization.text("editor.materials.tags"))
        if self._list.currentRow() < 0:
            self._status_label.setText(self._localization.text("editor.materials.select"))
        else:
            self.refresh_validation()
