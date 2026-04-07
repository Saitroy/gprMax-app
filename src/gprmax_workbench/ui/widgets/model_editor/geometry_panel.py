from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.model_entities import EDITOR_GEOMETRY_KINDS, default_geometry
from ....domain.models import GeometryPrimitive, Project
from ...layouts.flow_layout import FlowLayout
from ...splitters import configure_splitter
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_tags,
    tags_to_text,
)


class GeometryPanel(QWidget):
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
        self._list.currentRowChanged.connect(self._load_current_geometry)

        self._add_button = QPushButton()
        self._add_button.clicked.connect(self._add_geometry)
        self._duplicate_button = QPushButton()
        self._duplicate_button.clicked.connect(self._duplicate_geometry)
        self._delete_button = QPushButton()
        self._delete_button.clicked.connect(self._delete_geometry)

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

        self._label_edit = QLineEdit()
        self._kind_combo = QComboBox()
        for kind in EDITOR_GEOMETRY_KINDS:
            self._kind_combo.addItem(kind, kind)
        self._material_combo = QComboBox()
        self._dielectric_smoothing = QCheckBox()
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setFixedHeight(90)
        self._tags_edit = QLineEdit()
        self._status_label = build_status_label("")

        self._params_stack = QStackedWidget()
        self._box_fields = self._build_box_widget()
        self._sphere_fields = self._build_sphere_widget()
        self._cylinder_fields = self._build_cylinder_widget()

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self._label_label = QLabel()
        self._kind_label = QLabel()
        self._material_label = QLabel()
        self._parameters_label = QLabel()
        self._notes_label = QLabel()
        self._tags_label = QLabel()
        form.addRow(self._label_label, self._label_edit)
        form.addRow(self._kind_label, self._kind_combo)
        form.addRow(self._material_label, self._material_combo)
        form.addRow("", self._dielectric_smoothing)
        form.addRow(self._parameters_label, self._params_stack)
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
        splitter.setSizes([320, 680])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        for widget in (self._label_edit, self._tags_edit):
            widget.textChanged.connect(self._apply_changes)
        self._kind_combo.currentIndexChanged.connect(self._apply_changes)
        self._material_combo.currentIndexChanged.connect(self._apply_changes)
        self._dielectric_smoothing.toggled.connect(self._apply_changes)
        self._notes_edit.textChanged.connect(self._apply_changes)
        for widget in self._all_parameter_spinboxes():
            widget.valueChanged.connect(self._apply_changes)

        self.retranslate_ui()
        self.set_project(None)

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        self._list.clear()
        self.refresh_material_choices()
        if project is not None:
            for geometry in project.model.geometry:
                self._list.addItem(self._item_text(geometry))
        self._loading = False

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self._load_current_geometry(None)
        self._update_buttons()

    def refresh_material_choices(self) -> None:
        current_value = self._material_combo.currentData()
        self._loading = True
        self._material_combo.clear()
        project = self._model_editor_service.current_project()
        if project is not None:
            for material_id in self._model_editor_service.available_material_ids():
                self._material_combo.addItem(material_id, material_id)
        index = self._material_combo.findData(current_value)
        if index >= 0:
            self._material_combo.setCurrentIndex(index)
        elif self._material_combo.count() > 0:
            self._material_combo.setCurrentIndex(0)
        self._loading = False

    def refresh_validation(self) -> None:
        row = self._list.currentRow()
        prefixes = ["model.geometry"]
        if row >= 0:
            prefixes.insert(0, f"model.geometry[{row}]")
        self._status_label.setText(
            join_messages(
                self._validation_service.messages_for_prefixes(*prefixes),
                self._localization.text("editor.geometry.valid"),
            )
        )

    def _build_box_widget(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self._box_min_x = build_float_spinbox()
        self._box_min_y = build_float_spinbox()
        self._box_min_z = build_float_spinbox()
        self._box_max_x = build_float_spinbox()
        self._box_max_y = build_float_spinbox()
        self._box_max_z = build_float_spinbox()
        self._box_min_x_label = QLabel()
        self._box_min_y_label = QLabel()
        self._box_min_z_label = QLabel()
        self._box_max_x_label = QLabel()
        self._box_max_y_label = QLabel()
        self._box_max_z_label = QLabel()
        form.addRow(self._box_min_x_label, self._box_min_x)
        form.addRow(self._box_min_y_label, self._box_min_y)
        form.addRow(self._box_min_z_label, self._box_min_z)
        form.addRow(self._box_max_x_label, self._box_max_x)
        form.addRow(self._box_max_y_label, self._box_max_y)
        form.addRow(self._box_max_z_label, self._box_max_z)
        self._params_stack.addWidget(widget)
        return widget

    def _build_sphere_widget(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self._sphere_center_x = build_float_spinbox()
        self._sphere_center_y = build_float_spinbox()
        self._sphere_center_z = build_float_spinbox()
        self._sphere_radius = build_float_spinbox()
        self._sphere_center_x_label = QLabel()
        self._sphere_center_y_label = QLabel()
        self._sphere_center_z_label = QLabel()
        self._sphere_radius_label = QLabel()
        form.addRow(self._sphere_center_x_label, self._sphere_center_x)
        form.addRow(self._sphere_center_y_label, self._sphere_center_y)
        form.addRow(self._sphere_center_z_label, self._sphere_center_z)
        form.addRow(self._sphere_radius_label, self._sphere_radius)
        self._params_stack.addWidget(widget)
        return widget

    def _build_cylinder_widget(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self._cyl_start_x = build_float_spinbox()
        self._cyl_start_y = build_float_spinbox()
        self._cyl_start_z = build_float_spinbox()
        self._cyl_end_x = build_float_spinbox()
        self._cyl_end_y = build_float_spinbox()
        self._cyl_end_z = build_float_spinbox()
        self._cyl_radius = build_float_spinbox()
        self._cyl_start_x_label = QLabel()
        self._cyl_start_y_label = QLabel()
        self._cyl_start_z_label = QLabel()
        self._cyl_end_x_label = QLabel()
        self._cyl_end_y_label = QLabel()
        self._cyl_end_z_label = QLabel()
        self._cyl_radius_label = QLabel()
        form.addRow(self._cyl_start_x_label, self._cyl_start_x)
        form.addRow(self._cyl_start_y_label, self._cyl_start_y)
        form.addRow(self._cyl_start_z_label, self._cyl_start_z)
        form.addRow(self._cyl_end_x_label, self._cyl_end_x)
        form.addRow(self._cyl_end_y_label, self._cyl_end_y)
        form.addRow(self._cyl_end_z_label, self._cyl_end_z)
        form.addRow(self._cyl_radius_label, self._cyl_radius)
        self._params_stack.addWidget(widget)
        return widget

    def _all_parameter_spinboxes(self) -> list[QWidget]:
        return [
            self._box_min_x,
            self._box_min_y,
            self._box_min_z,
            self._box_max_x,
            self._box_max_y,
            self._box_max_z,
            self._sphere_center_x,
            self._sphere_center_y,
            self._sphere_center_z,
            self._sphere_radius,
            self._cyl_start_x,
            self._cyl_start_y,
            self._cyl_start_z,
            self._cyl_end_x,
            self._cyl_end_y,
            self._cyl_end_z,
            self._cyl_radius,
        ]

    def _load_current_geometry(self, row: int | None) -> None:
        project = self._model_editor_service.current_project()
        self._loading = True
        enabled = (
            project is not None
            and row is not None
            and 0 <= row < len(project.model.geometry)
        )
        for widget in (
            self._label_edit,
            self._kind_combo,
            self._material_combo,
            self._dielectric_smoothing,
            self._notes_edit,
            self._tags_edit,
        ):
            widget.setEnabled(enabled)
        for widget in self._all_parameter_spinboxes():
            widget.setEnabled(enabled)

        if not enabled or project is None:
            self._label_edit.clear()
            self._kind_combo.setCurrentIndex(0)
            self._notes_edit.clear()
            self._tags_edit.clear()
            self._dielectric_smoothing.setChecked(True)
            for widget in self._all_parameter_spinboxes():
                widget.setValue(0.0)
            self._loading = False
            self.refresh_validation()
            self._update_buttons()
            return

        geometry = project.model.geometry[row]
        self._label_edit.setText(geometry.label)
        self._kind_combo.setCurrentText(geometry.kind)
        material_id = geometry.material_ids[0] if geometry.material_ids else ""
        material_index = self._material_combo.findData(material_id)
        if material_index >= 0:
            self._material_combo.setCurrentIndex(material_index)
        self._dielectric_smoothing.setChecked(geometry.dielectric_smoothing)
        self._notes_edit.setPlainText(geometry.notes)
        self._tags_edit.setText(tags_to_text(geometry.tags))
        self._set_parameters_from_geometry(geometry)
        self._loading = False
        self.refresh_validation()
        self._update_buttons()

    def _set_parameters_from_geometry(self, geometry: GeometryPrimitive) -> None:
        if geometry.kind == "sphere":
            self._params_stack.setCurrentWidget(self._sphere_fields)
            center = geometry.parameters.get("center_m", {})
            self._sphere_center_x.setValue(float(center.get("x", 0.0)))
            self._sphere_center_y.setValue(float(center.get("y", 0.0)))
            self._sphere_center_z.setValue(float(center.get("z", 0.0)))
            self._sphere_radius.setValue(float(geometry.parameters.get("radius_m", 0.0)))
            return

        if geometry.kind == "cylinder":
            self._params_stack.setCurrentWidget(self._cylinder_fields)
            start = geometry.parameters.get("start_m", {})
            end = geometry.parameters.get("end_m", {})
            self._cyl_start_x.setValue(float(start.get("x", 0.0)))
            self._cyl_start_y.setValue(float(start.get("y", 0.0)))
            self._cyl_start_z.setValue(float(start.get("z", 0.0)))
            self._cyl_end_x.setValue(float(end.get("x", 0.0)))
            self._cyl_end_y.setValue(float(end.get("y", 0.0)))
            self._cyl_end_z.setValue(float(end.get("z", 0.0)))
            self._cyl_radius.setValue(float(geometry.parameters.get("radius_m", 0.0)))
            return

        self._params_stack.setCurrentWidget(self._box_fields)
        lower_left = geometry.parameters.get("lower_left_m", {})
        upper_right = geometry.parameters.get("upper_right_m", {})
        self._box_min_x.setValue(float(lower_left.get("x", 0.0)))
        self._box_min_y.setValue(float(lower_left.get("y", 0.0)))
        self._box_min_z.setValue(float(lower_left.get("z", 0.0)))
        self._box_max_x.setValue(float(upper_right.get("x", 0.0)))
        self._box_max_y.setValue(float(upper_right.get("y", 0.0)))
        self._box_max_z.setValue(float(upper_right.get("z", 0.0)))

    def _apply_changes(self) -> None:
        row = self._list.currentRow()
        project = self._model_editor_service.current_project()
        if self._loading or project is None or not (0 <= row < len(project.model.geometry)):
            return

        current = project.model.geometry[row]
        selected_kind = self._kind_combo.currentText()
        if selected_kind != current.kind:
            geometry = default_geometry(project, row + 1, kind=selected_kind)
            geometry.label = self._label_edit.text() or geometry.label
            geometry.material_ids = [str(self._material_combo.currentData() or "")]
            geometry.dielectric_smoothing = self._dielectric_smoothing.isChecked()
            geometry.notes = self._notes_edit.toPlainText()
            geometry.tags = parse_tags(self._tags_edit.text())
        else:
            geometry = GeometryPrimitive(
                kind=selected_kind,
                label=self._label_edit.text(),
                material_ids=[str(self._material_combo.currentData() or "")],
                dielectric_smoothing=self._dielectric_smoothing.isChecked(),
                notes=self._notes_edit.toPlainText(),
                tags=parse_tags(self._tags_edit.text()),
                parameters=self._parameters_for_kind(selected_kind),
            )

        self._model_editor_service.update_geometry(row, geometry)
        self._list.item(row).setText(self._item_text(geometry))
        self._loading = True
        self._set_parameters_from_geometry(geometry)
        self._loading = False
        self.refresh_validation()
        self.model_changed.emit()

    def _parameters_for_kind(self, kind: str) -> dict[str, object]:
        if kind == "sphere":
            return {
                "center_m": {
                    "x": self._sphere_center_x.value(),
                    "y": self._sphere_center_y.value(),
                    "z": self._sphere_center_z.value(),
                },
                "radius_m": self._sphere_radius.value(),
            }
        if kind == "cylinder":
            return {
                "start_m": {
                    "x": self._cyl_start_x.value(),
                    "y": self._cyl_start_y.value(),
                    "z": self._cyl_start_z.value(),
                },
                "end_m": {
                    "x": self._cyl_end_x.value(),
                    "y": self._cyl_end_y.value(),
                    "z": self._cyl_end_z.value(),
                },
                "radius_m": self._cyl_radius.value(),
            }
        return {
            "lower_left_m": {
                "x": self._box_min_x.value(),
                "y": self._box_min_y.value(),
                "z": self._box_min_z.value(),
            },
            "upper_right_m": {
                "x": self._box_max_x.value(),
                "y": self._box_max_y.value(),
                "z": self._box_max_z.value(),
            },
        }

    def _add_geometry(self) -> None:
        index = self._model_editor_service.add_geometry()
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _duplicate_geometry(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        index = self._model_editor_service.duplicate_geometry(row)
        self.set_project(self._model_editor_service.current_project())
        self._list.setCurrentRow(index)
        self.model_changed.emit()

    def _delete_geometry(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        next_index = self._model_editor_service.delete_geometry(row)
        self.set_project(self._model_editor_service.current_project())
        if next_index is not None:
            self._list.setCurrentRow(next_index)
        self.model_changed.emit()

    def _item_text(self, geometry: GeometryPrimitive) -> str:
        material = (
            geometry.material_ids[0]
            if geometry.material_ids
            else self._localization.text("editor.geometry.no_material")
        )
        return f"{geometry.label or geometry.kind} | {geometry.kind} | {material}"

    def _update_buttons(self) -> None:
        enabled = self._list.currentRow() >= 0
        self._duplicate_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)

    def retranslate_ui(self) -> None:
        self._list_title.setText(self._localization.text("editor.geometry.list_title"))
        self._add_button.setText(self._localization.text("common.add"))
        self._duplicate_button.setText(self._localization.text("common.duplicate"))
        self._delete_button.setText(self._localization.text("common.delete"))
        self._label_label.setText(self._localization.text("editor.geometry.label"))
        self._kind_label.setText(self._localization.text("editor.geometry.kind"))
        self._material_label.setText(self._localization.text("editor.geometry.material"))
        self._dielectric_smoothing.setText(
            self._localization.text("editor.geometry.smoothing")
        )
        self._parameters_label.setText(
            self._localization.text("editor.geometry.parameters")
        )
        self._notes_label.setText(self._localization.text("editor.geometry.notes"))
        self._tags_label.setText(self._localization.text("editor.geometry.tags"))
        self._box_min_x_label.setText(self._localization.text("editor.geometry.box.lower_left_x"))
        self._box_min_y_label.setText(self._localization.text("editor.geometry.box.lower_left_y"))
        self._box_min_z_label.setText(self._localization.text("editor.geometry.box.lower_left_z"))
        self._box_max_x_label.setText(self._localization.text("editor.geometry.box.upper_right_x"))
        self._box_max_y_label.setText(self._localization.text("editor.geometry.box.upper_right_y"))
        self._box_max_z_label.setText(self._localization.text("editor.geometry.box.upper_right_z"))
        self._sphere_center_x_label.setText(self._localization.text("editor.geometry.sphere.center_x"))
        self._sphere_center_y_label.setText(self._localization.text("editor.geometry.sphere.center_y"))
        self._sphere_center_z_label.setText(self._localization.text("editor.geometry.sphere.center_z"))
        self._sphere_radius_label.setText(self._localization.text("editor.geometry.radius"))
        self._cyl_start_x_label.setText(self._localization.text("editor.geometry.cylinder.start_x"))
        self._cyl_start_y_label.setText(self._localization.text("editor.geometry.cylinder.start_y"))
        self._cyl_start_z_label.setText(self._localization.text("editor.geometry.cylinder.start_z"))
        self._cyl_end_x_label.setText(self._localization.text("editor.geometry.cylinder.end_x"))
        self._cyl_end_y_label.setText(self._localization.text("editor.geometry.cylinder.end_y"))
        self._cyl_end_z_label.setText(self._localization.text("editor.geometry.cylinder.end_z"))
        self._cyl_radius_label.setText(self._localization.text("editor.geometry.radius"))
        if self._list.currentRow() < 0:
            self._status_label.setText(self._localization.text("editor.geometry.select"))
        else:
            self.refresh_validation()
