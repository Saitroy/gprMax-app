from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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


@dataclass(frozen=True, slots=True)
class _MaterialPreset:
    key: str
    identifier: str
    relative_permittivity: float
    conductivity: float
    color: str


_MATERIAL_PRESETS = (
    _MaterialPreset("air", "air", 1.0, 0.0, "#d8eff8"),
    _MaterialPreset("dry_sand", "dry_sand", 3.0, 0.0001, "#d8b46a"),
    _MaterialPreset("wet_soil", "wet_soil", 15.0, 0.03, "#7a5b3a"),
    _MaterialPreset("concrete", "concrete", 6.0, 0.01, "#9aa3a8"),
    _MaterialPreset("fresh_water", "fresh_water", 80.0, 0.001, "#4ba3c7"),
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

        self._preset_buttons: dict[str, QPushButton] = {}

        presets_card = QFrame()
        presets_card.setObjectName("ViewCard")
        presets_layout = QVBoxLayout(presets_card)
        presets_layout.setContentsMargins(14, 12, 14, 12)
        presets_layout.setSpacing(8)
        self._presets_title = QLabel()
        self._presets_title.setObjectName("SectionTitle")
        self._presets_hint = QLabel()
        self._presets_hint.setObjectName("SectionBody")
        self._presets_hint.setWordWrap(True)
        presets_buttons = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        for preset in _MATERIAL_PRESETS:
            button = QPushButton()
            button.setIcon(self._material_icon(preset.color))
            button.clicked.connect(
                lambda _checked=False, item=preset: self._apply_preset(item)
            )
            self._preset_buttons[preset.key] = button
            presets_buttons.addWidget(button)
        presets_layout.addWidget(self._presets_title)
        presets_layout.addWidget(self._presets_hint)
        presets_layout.addLayout(presets_buttons)

        self._list = QListWidget()
        self._list.setSpacing(8)
        self._list.setIconSize(QSize(34, 34))
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
        list_layout.setSpacing(10)
        self._list_title = QLabel()
        self._list_subtitle = QLabel()
        self._list_subtitle.setObjectName("SectionBody")
        self._list_subtitle.setWordWrap(True)
        list_layout.addWidget(self._list_title)
        list_layout.addWidget(self._list_subtitle)
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
        self._hint_label = QLabel()
        self._hint_label.setWordWrap(True)
        self._hint_label.setObjectName("SectionBody")
        self._preview_card = QFrame()
        self._preview_card.setObjectName("ViewCard")
        self._preview_card.setStyleSheet(
            """
            QFrame#MaterialSwatch {
                border: 1px solid #c4d1dc;
                border-radius: 14px;
                min-width: 72px;
                min-height: 56px;
            }
            """
        )
        preview_layout = QHBoxLayout(self._preview_card)
        preview_layout.setContentsMargins(14, 12, 14, 12)
        preview_layout.setSpacing(12)
        self._preview_swatch = QFrame()
        self._preview_swatch.setObjectName("MaterialSwatch")
        self._preview_summary = QLabel()
        self._preview_summary.setWordWrap(True)
        self._usage_label = QLabel()
        self._usage_label.setObjectName("SectionBody")
        self._usage_label.setWordWrap(True)
        preview_text = QVBoxLayout()
        preview_text.setContentsMargins(0, 0, 0, 0)
        preview_text.setSpacing(4)
        preview_text.addWidget(self._preview_summary)
        preview_text.addWidget(self._usage_label)
        preview_layout.addWidget(self._preview_swatch)
        preview_layout.addLayout(preview_text, 1)

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(10)
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
        detail_layout.addWidget(self._hint_label)
        detail_layout.addWidget(self._preview_card)
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
        layout.setSpacing(12)
        layout.addWidget(presets_card)
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
                self._list.addItem(self._build_material_item(material))
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
            self._refresh_preview(None)
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
        self._refresh_preview(material)
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
        self._update_material_item(row, material)
        self._refresh_preview(material)
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

    def _apply_preset(self, preset: _MaterialPreset) -> None:
        project = self._model_editor_service.current_project()
        if project is None:
            return
        row = self._list.currentRow()
        if row < 0:
            row = self._model_editor_service.add_material()
            self.set_project(project)
            self._list.setCurrentRow(row)

        existing = [
            material.identifier
            for index, material in enumerate(project.model.materials)
            if index != row
        ]
        identifier = self._unique_identifier(preset.identifier, existing)
        material = MaterialDefinition(
            identifier=identifier,
            relative_permittivity=preset.relative_permittivity,
            conductivity=preset.conductivity,
            relative_permeability=1.0,
            magnetic_loss=0.0,
            notes=self._localization.text(f"editor.materials.preset_note.{preset.key}"),
            tags=[self._localization.text("editor.materials.preset_tag")],
        )
        self._model_editor_service.update_material(row, material)
        self.set_project(project)
        self._list.setCurrentRow(row)
        self.model_changed.emit()

    def _build_material_item(self, material: MaterialDefinition) -> QListWidgetItem:
        item = QListWidgetItem(self._item_text(material))
        item.setIcon(self._material_icon(self._material_color(material).name()))
        item.setSizeHint(QSize(220, 64))
        return item

    def _update_material_item(self, row: int, material: MaterialDefinition) -> None:
        item = self._list.item(row)
        if item is None:
            return
        item.setText(self._item_text(material))
        item.setIcon(self._material_icon(self._material_color(material).name()))

    def _item_text(self, material: MaterialDefinition) -> str:
        return (
            f"{material.identifier or self._localization.text('editor.materials.unnamed')}\n"
            f"er {material.relative_permittivity:.3g} | "
            f"sigma {material.conductivity:.3g} S/m"
        )

    def _refresh_preview(self, material: MaterialDefinition | None) -> None:
        if material is None:
            self._preview_swatch.setStyleSheet("background: #eef3f7;")
            self._preview_summary.setText(
                self._localization.text("editor.materials.preview.empty")
            )
            self._usage_label.setText("")
            return
        color = self._material_color(material).name()
        self._preview_swatch.setStyleSheet(f"background: {color};")
        self._preview_summary.setText(
            self._localization.text(
                "editor.materials.preview.summary",
                name=material.identifier
                or self._localization.text("editor.materials.unnamed"),
                permittivity=f"{material.relative_permittivity:.3g}",
                conductivity=f"{material.conductivity:.3g}",
            )
        )
        self._usage_label.setText(
            self._localization.text(
                "editor.materials.usage",
                count=self._material_usage_count(material.identifier),
            )
        )

    def _material_usage_count(self, identifier: str) -> int:
        project = self._model_editor_service.current_project()
        if project is None or not identifier.strip():
            return 0
        return sum(
            1
            for geometry in project.model.geometry
            if identifier in geometry.material_ids
        )

    def _material_color(self, material: MaterialDefinition) -> QColor:
        for preset in _MATERIAL_PRESETS:
            if material.identifier == preset.identifier:
                return QColor(preset.color)
        palette = (
            "#3f7aa8",
            "#5f8f51",
            "#9b6a4c",
            "#7b63ad",
            "#0f766e",
            "#c1702d",
            "#51719b",
            "#8b5e83",
        )
        seed = material.identifier or f"{material.relative_permittivity}:{material.conductivity}"
        return QColor(palette[sum(ord(char) for char in seed) % len(palette)])

    def _material_icon(self, color: str) -> QIcon:
        pixmap = QPixmap(34, 34)
        pixmap.fill(QColor(color))
        return QIcon(pixmap)

    def _unique_identifier(self, base: str, existing: list[str]) -> str:
        if base not in existing:
            return base
        suffix = 2
        while f"{base}_{suffix}" in existing:
            suffix += 1
        return f"{base}_{suffix}"

    def _update_buttons(self) -> None:
        enabled = self._list.currentRow() >= 0
        self._duplicate_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)

    def retranslate_ui(self) -> None:
        self._list_title.setText(self._localization.text("editor.materials.list_title"))
        self._list_subtitle.setText(
            self._localization.text("editor.materials.list_subtitle")
        )
        self._presets_title.setText(self._localization.text("editor.materials.presets_title"))
        self._presets_hint.setText(self._localization.text("editor.materials.presets_hint"))
        for preset in _MATERIAL_PRESETS:
            button = self._preset_buttons[preset.key]
            button.setText(self._localization.text(f"editor.materials.preset.{preset.key}"))
            button.setToolTip(
                self._localization.text(
                    "editor.materials.preset_tooltip",
                    permittivity=f"{preset.relative_permittivity:.3g}",
                    conductivity=f"{preset.conductivity:.3g}",
                )
            )
        self._hint_label.setText(self._localization.text("editor.materials.hint"))
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
            self._refresh_preview(None)
        else:
            row = self._list.currentRow()
            project = self._model_editor_service.current_project()
            if project is not None and 0 <= row < len(project.model.materials):
                self._refresh_preview(project.model.materials[row])
            self.refresh_validation()
