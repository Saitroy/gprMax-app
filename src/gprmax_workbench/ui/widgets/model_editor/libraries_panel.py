from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.model_entities import ANTENNA_LIBRARY_CATALOG, antenna_catalog_entry
from ....domain.models import (
    AntennaModelDefinition,
    GeometryImportDefinition,
    Project,
    Vector3,
)
from ...layouts.flow_layout import FlowLayout
from ...splitters import configure_splitter
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_tags,
    tags_to_text,
)


class LibrariesPanel(QWidget):
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

        self._tabs = QTabWidget()
        self._tabs.currentChanged.connect(self.refresh_validation)
        self._tabs.addTab(self._build_imports_tab(), "")
        self._tabs.addTab(self._build_antennas_tab(), "")

        self._status_label = build_status_label("")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._tabs, 1)
        layout.addWidget(self._status_label)

        self.retranslate_ui()
        self.set_project(None)

    def _build_imports_tab(self) -> QWidget:
        self._imports_list = QListWidget()
        self._imports_list.currentRowChanged.connect(self._load_current_import)
        self._add_import_button = QPushButton()
        self._add_import_button.clicked.connect(self._add_import)
        self._duplicate_import_button = QPushButton()
        self._duplicate_import_button.clicked.connect(self._duplicate_import)
        self._delete_import_button = QPushButton()
        self._delete_import_button.clicked.connect(self._delete_import)

        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        self._imports_list_title = QLabel()
        list_layout.addWidget(self._imports_list_title)
        list_layout.addWidget(self._imports_list, 1)
        import_buttons = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        import_buttons.addWidget(self._add_import_button)
        import_buttons.addWidget(self._duplicate_import_button)
        import_buttons.addWidget(self._delete_import_button)
        list_layout.addLayout(import_buttons)

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self._import_id = QLineEdit()
        self._import_geometry_file = QLineEdit()
        self._import_geometry_browse = QPushButton()
        self._import_geometry_browse.clicked.connect(self._browse_geometry_file)
        self._import_materials_file = QLineEdit()
        self._import_materials_browse = QPushButton()
        self._import_materials_browse.clicked.connect(self._browse_materials_file)
        self._import_pos_x = build_float_spinbox()
        self._import_pos_y = build_float_spinbox()
        self._import_pos_z = build_float_spinbox()
        self._import_smoothing = QCheckBox()
        self._import_notes = QPlainTextEdit()
        self._import_notes.setFixedHeight(90)
        self._import_tags = QLineEdit()
        self._import_id_label = QLabel()
        self._import_geometry_label = QLabel()
        self._import_materials_label = QLabel()
        self._import_pos_x_label = QLabel()
        self._import_pos_y_label = QLabel()
        self._import_pos_z_label = QLabel()
        self._import_notes_label = QLabel()
        self._import_tags_label = QLabel()
        self._import_preview_label = QLabel()
        self._import_preview_label.setWordWrap(True)
        geometry_file_row = QWidget()
        geometry_file_layout = QHBoxLayout(geometry_file_row)
        geometry_file_layout.setContentsMargins(0, 0, 0, 0)
        geometry_file_layout.addWidget(self._import_geometry_file, 1)
        geometry_file_layout.addWidget(self._import_geometry_browse)
        materials_file_row = QWidget()
        materials_file_layout = QHBoxLayout(materials_file_row)
        materials_file_layout.setContentsMargins(0, 0, 0, 0)
        materials_file_layout.addWidget(self._import_materials_file, 1)
        materials_file_layout.addWidget(self._import_materials_browse)
        form.addRow(self._import_id_label, self._import_id)
        form.addRow(self._import_geometry_label, geometry_file_row)
        form.addRow(self._import_materials_label, materials_file_row)
        form.addRow(self._import_pos_x_label, self._import_pos_x)
        form.addRow(self._import_pos_y_label, self._import_pos_y)
        form.addRow(self._import_pos_z_label, self._import_pos_z)
        form.addRow("", self._import_smoothing)
        form.addRow(self._import_notes_label, self._import_notes)
        form.addRow(self._import_tags_label, self._import_tags)
        detail_layout.addLayout(form)
        detail_layout.addWidget(self._import_preview_label)
        detail_layout.addStretch(1)

        splitter = configure_splitter(QSplitter())
        splitter.addWidget(list_panel)
        splitter.addWidget(detail_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 800])

        for widget in (
            self._import_id,
            self._import_geometry_file,
            self._import_materials_file,
            self._import_tags,
        ):
            widget.textChanged.connect(self._apply_import_changes)
        for widget in (self._import_pos_x, self._import_pos_y, self._import_pos_z):
            widget.valueChanged.connect(self._apply_import_changes)
        self._import_smoothing.toggled.connect(self._apply_import_changes)
        self._import_notes.textChanged.connect(self._apply_import_changes)

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(splitter)
        return tab

    def _build_antennas_tab(self) -> QWidget:
        self._antennas_list = QListWidget()
        self._antennas_list.currentRowChanged.connect(self._load_current_antenna)
        self._add_antenna_button = QPushButton()
        self._add_antenna_button.clicked.connect(self._add_antenna)
        self._duplicate_antenna_button = QPushButton()
        self._duplicate_antenna_button.clicked.connect(self._duplicate_antenna)
        self._delete_antenna_button = QPushButton()
        self._delete_antenna_button.clicked.connect(self._delete_antenna)

        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        self._antennas_list_title = QLabel()
        list_layout.addWidget(self._antennas_list_title)
        list_layout.addWidget(self._antennas_list, 1)
        antenna_buttons = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        antenna_buttons.addWidget(self._add_antenna_button)
        antenna_buttons.addWidget(self._duplicate_antenna_button)
        antenna_buttons.addWidget(self._delete_antenna_button)
        list_layout.addLayout(antenna_buttons)

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self._antenna_id = QLineEdit()
        self._antenna_library = QComboBox()
        self._antenna_library.currentIndexChanged.connect(self._populate_antenna_models)
        self._antenna_model = QComboBox()
        self._antenna_model.currentIndexChanged.connect(self._apply_catalog_defaults)
        self._antenna_module = QLineEdit()
        self._antenna_function = QLineEdit()
        self._antenna_pos_x = build_float_spinbox()
        self._antenna_pos_y = build_float_spinbox()
        self._antenna_pos_z = build_float_spinbox()
        self._antenna_resolution = build_float_spinbox(minimum=0.0001, step=0.0005)
        self._antenna_rotate = QCheckBox()
        self._antenna_notes = QPlainTextEdit()
        self._antenna_notes.setFixedHeight(90)
        self._antenna_tags = QLineEdit()
        self._antenna_id_label = QLabel()
        self._antenna_library_label = QLabel()
        self._antenna_model_label = QLabel()
        self._antenna_module_label = QLabel()
        self._antenna_function_label = QLabel()
        self._antenna_pos_x_label = QLabel()
        self._antenna_pos_y_label = QLabel()
        self._antenna_pos_z_label = QLabel()
        self._antenna_resolution_label = QLabel()
        self._antenna_notes_label = QLabel()
        self._antenna_tags_label = QLabel()
        self._antenna_catalog_summary = QLabel()
        self._antenna_catalog_summary.setWordWrap(True)
        self._antenna_preview_label = QLabel()
        self._antenna_preview_label.setWordWrap(True)
        form.addRow(self._antenna_id_label, self._antenna_id)
        form.addRow(self._antenna_library_label, self._antenna_library)
        form.addRow(self._antenna_model_label, self._antenna_model)
        form.addRow(self._antenna_module_label, self._antenna_module)
        form.addRow(self._antenna_function_label, self._antenna_function)
        form.addRow(self._antenna_pos_x_label, self._antenna_pos_x)
        form.addRow(self._antenna_pos_y_label, self._antenna_pos_y)
        form.addRow(self._antenna_pos_z_label, self._antenna_pos_z)
        form.addRow(self._antenna_resolution_label, self._antenna_resolution)
        form.addRow("", self._antenna_rotate)
        form.addRow(self._antenna_notes_label, self._antenna_notes)
        form.addRow(self._antenna_tags_label, self._antenna_tags)
        detail_layout.addLayout(form)
        detail_layout.addWidget(self._antenna_catalog_summary)
        detail_layout.addWidget(self._antenna_preview_label)
        detail_layout.addStretch(1)

        splitter = configure_splitter(QSplitter())
        splitter.addWidget(list_panel)
        splitter.addWidget(detail_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 800])

        for widget in (
            self._antenna_id,
            self._antenna_module,
            self._antenna_function,
            self._antenna_tags,
        ):
            widget.textChanged.connect(self._apply_antenna_changes)
        for widget in (
            self._antenna_pos_x,
            self._antenna_pos_y,
            self._antenna_pos_z,
            self._antenna_resolution,
        ):
            widget.valueChanged.connect(self._apply_antenna_changes)
        self._antenna_rotate.toggled.connect(self._apply_antenna_changes)
        self._antenna_notes.textChanged.connect(self._apply_antenna_changes)
        self._antenna_library.currentIndexChanged.connect(self._apply_antenna_changes)
        self._antenna_model.currentIndexChanged.connect(self._apply_antenna_changes)

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(splitter)
        return tab

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        self._imports_list.clear()
        self._antennas_list.clear()
        self._populate_libraries()
        if project is not None:
            for item in project.model.geometry_imports:
                self._imports_list.addItem(self._import_item_text(item))
            for item in project.model.antenna_models:
                self._antennas_list.addItem(self._antenna_item_text(item))
        self._loading = False
        self._imports_list.setCurrentRow(0 if self._imports_list.count() else -1)
        self._antennas_list.setCurrentRow(0 if self._antennas_list.count() else -1)
        self._update_import_preview()
        self._update_antenna_preview()
        self.refresh_validation()

    def refresh_validation(self) -> None:
        if not hasattr(self, "_status_label"):
            return
        prefixes = ["model.geometry_imports", "model.antenna_models"]
        if self._tabs.currentIndex() == 0 and self._imports_list.currentRow() >= 0:
            prefixes.insert(0, f"model.geometry_imports[{self._imports_list.currentRow()}]")
        if self._tabs.currentIndex() == 1 and self._antennas_list.currentRow() >= 0:
            prefixes.insert(0, f"model.antenna_models[{self._antennas_list.currentRow()}]")
        self._status_label.setText(
            join_messages(
                self._validation_service.messages_for_prefixes(*prefixes),
                self._localization.text("editor.libraries.valid"),
            )
        )

    def retranslate_ui(self) -> None:
        self._tabs.setTabText(0, self._localization.text("editor.libraries.imports_tab"))
        self._tabs.setTabText(1, self._localization.text("editor.libraries.antennas_tab"))
        self._imports_list_title.setText(self._localization.text("editor.libraries.imports"))
        self._add_import_button.setText(self._localization.text("common.add"))
        self._duplicate_import_button.setText(self._localization.text("common.duplicate"))
        self._delete_import_button.setText(self._localization.text("common.delete"))
        self._import_id_label.setText(self._localization.text("editor.libraries.identifier"))
        self._import_geometry_label.setText(self._localization.text("editor.libraries.geometry_file"))
        self._import_materials_label.setText(self._localization.text("editor.libraries.materials_file"))
        self._import_geometry_browse.setText(self._localization.text("common.browse"))
        self._import_materials_browse.setText(self._localization.text("common.browse"))
        self._import_pos_x_label.setText(self._localization.text("editor.scene.position_x"))
        self._import_pos_y_label.setText(self._localization.text("editor.scene.position_y"))
        self._import_pos_z_label.setText(self._localization.text("editor.scene.position_z"))
        self._import_smoothing.setText(self._localization.text("editor.libraries.smoothing"))
        self._import_notes_label.setText(self._localization.text("editor.common.notes"))
        self._import_tags_label.setText(self._localization.text("editor.common.tags"))
        self._import_preview_label.setText(self._localization.text("editor.libraries.no_import_preview"))
        self._antennas_list_title.setText(self._localization.text("editor.libraries.antennas"))
        self._add_antenna_button.setText(self._localization.text("common.add"))
        self._duplicate_antenna_button.setText(self._localization.text("common.duplicate"))
        self._delete_antenna_button.setText(self._localization.text("common.delete"))
        self._antenna_id_label.setText(self._localization.text("editor.libraries.identifier"))
        self._antenna_library_label.setText(self._localization.text("editor.libraries.library"))
        self._antenna_model_label.setText(self._localization.text("editor.libraries.model"))
        self._antenna_module_label.setText(self._localization.text("editor.libraries.module"))
        self._antenna_function_label.setText(self._localization.text("editor.libraries.function"))
        self._antenna_pos_x_label.setText(self._localization.text("editor.scene.position_x"))
        self._antenna_pos_y_label.setText(self._localization.text("editor.scene.position_y"))
        self._antenna_pos_z_label.setText(self._localization.text("editor.scene.position_z"))
        self._antenna_resolution_label.setText(self._localization.text("editor.libraries.resolution"))
        self._antenna_rotate.setText(self._localization.text("editor.libraries.rotate90"))
        self._antenna_notes_label.setText(self._localization.text("editor.common.notes"))
        self._antenna_tags_label.setText(self._localization.text("editor.common.tags"))
        self._antenna_catalog_summary.setText(self._localization.text("editor.libraries.no_catalog_preview"))
        self._antenna_preview_label.setText(self._localization.text("editor.libraries.no_antenna_preview"))
        self.refresh_validation()

    def _populate_libraries(self) -> None:
        current = self._antenna_library.currentData()
        self._antenna_library.blockSignals(True)
        self._antenna_library.clear()
        for library_key in ANTENNA_LIBRARY_CATALOG:
            self._antenna_library.addItem(library_key, library_key)
        self._antenna_library.blockSignals(False)
        index = self._antenna_library.findData(current)
        self._antenna_library.setCurrentIndex(index if index >= 0 else 0)
        self._populate_antenna_models()

    def _populate_antenna_models(self) -> None:
        library = str(self._antenna_library.currentData() or "")
        current_model = self._antenna_model.currentData()
        self._antenna_model.blockSignals(True)
        self._antenna_model.clear()
        for model_key, metadata in ANTENNA_LIBRARY_CATALOG.get(library, {}).items():
            self._antenna_model.addItem(str(metadata["label"]), model_key)
        self._antenna_model.blockSignals(False)
        index = self._antenna_model.findData(current_model)
        self._antenna_model.setCurrentIndex(index if index >= 0 else 0)

    def _apply_catalog_defaults(self) -> None:
        if self._loading:
            return
        library = str(self._antenna_library.currentData() or "")
        model_key = str(self._antenna_model.currentData() or "")
        metadata = ANTENNA_LIBRARY_CATALOG.get(library, {}).get(model_key)
        if metadata is None:
            return
        self._loading = True
        self._antenna_module.setText(str(metadata["module_path"]))
        self._antenna_function.setText(str(metadata["function_name"]))
        self._antenna_resolution.setValue(float(metadata["resolution_m"]))
        self._loading = False
        self._update_antenna_preview()

    def _load_current_import(self, row: int) -> None:
        project = self._model_editor_service.current_project()
        self._loading = True
        enabled = project is not None and 0 <= row < len(project.model.geometry_imports)
        for widget in (
            self._import_id,
            self._import_geometry_file,
            self._import_materials_file,
            self._import_pos_x,
            self._import_pos_y,
            self._import_pos_z,
            self._import_smoothing,
            self._import_notes,
            self._import_tags,
            self._import_geometry_browse,
            self._import_materials_browse,
        ):
            widget.setEnabled(enabled)
        if not enabled or project is None:
            self._import_id.clear()
            self._import_geometry_file.clear()
            self._import_materials_file.clear()
            self._import_pos_x.setValue(0.0)
            self._import_pos_y.setValue(0.0)
            self._import_pos_z.setValue(0.0)
            self._import_smoothing.setChecked(False)
            self._import_notes.clear()
            self._import_tags.clear()
            self._loading = False
            self._update_import_preview()
            self.refresh_validation()
            return
        item = project.model.geometry_imports[row]
        self._import_id.setText(item.identifier)
        self._import_geometry_file.setText(item.geometry_hdf5)
        self._import_materials_file.setText(item.materials_file)
        self._import_pos_x.setValue(item.position_m.x)
        self._import_pos_y.setValue(item.position_m.y)
        self._import_pos_z.setValue(item.position_m.z)
        self._import_smoothing.setChecked(item.dielectric_smoothing)
        self._import_notes.setPlainText(item.notes)
        self._import_tags.setText(tags_to_text(item.tags))
        self._loading = False
        self._update_import_preview()
        self.refresh_validation()

    def _load_current_antenna(self, row: int) -> None:
        project = self._model_editor_service.current_project()
        self._loading = True
        enabled = project is not None and 0 <= row < len(project.model.antenna_models)
        for widget in (
            self._antenna_id,
            self._antenna_library,
            self._antenna_model,
            self._antenna_module,
            self._antenna_function,
            self._antenna_pos_x,
            self._antenna_pos_y,
            self._antenna_pos_z,
            self._antenna_resolution,
            self._antenna_rotate,
            self._antenna_notes,
            self._antenna_tags,
        ):
            widget.setEnabled(enabled)
        if not enabled or project is None:
            self._antenna_id.clear()
            self._antenna_module.clear()
            self._antenna_function.clear()
            self._antenna_pos_x.setValue(0.0)
            self._antenna_pos_y.setValue(0.0)
            self._antenna_pos_z.setValue(0.0)
            self._antenna_resolution.setValue(0.001)
            self._antenna_rotate.setChecked(False)
            self._antenna_notes.clear()
            self._antenna_tags.clear()
            self._loading = False
            self._update_antenna_preview()
            self.refresh_validation()
            return
        antenna = project.model.antenna_models[row]
        self._antenna_id.setText(antenna.identifier)
        library_index = self._antenna_library.findData(antenna.library)
        if library_index >= 0:
            self._antenna_library.setCurrentIndex(library_index)
            self._populate_antenna_models()
        model_index = self._antenna_model.findData(antenna.model_key)
        if model_index >= 0:
            self._antenna_model.setCurrentIndex(model_index)
        self._antenna_module.setText(antenna.module_path)
        self._antenna_function.setText(antenna.function_name)
        self._antenna_pos_x.setValue(antenna.position_m.x)
        self._antenna_pos_y.setValue(antenna.position_m.y)
        self._antenna_pos_z.setValue(antenna.position_m.z)
        self._antenna_resolution.setValue(antenna.resolution_m)
        self._antenna_rotate.setChecked(antenna.rotate90)
        self._antenna_notes.setPlainText(antenna.notes)
        self._antenna_tags.setText(tags_to_text(antenna.tags))
        self._loading = False
        self._update_antenna_preview()
        self.refresh_validation()

    def _apply_import_changes(self) -> None:
        row = self._imports_list.currentRow()
        project = self._model_editor_service.current_project()
        if self._loading or project is None or not (0 <= row < len(project.model.geometry_imports)):
            return
        self._model_editor_service.update_geometry_import(
            row,
            GeometryImportDefinition(
                identifier=self._import_id.text().strip(),
                position_m=Vector3(
                    x=self._import_pos_x.value(),
                    y=self._import_pos_y.value(),
                    z=self._import_pos_z.value(),
                ),
                geometry_hdf5=self._import_geometry_file.text().strip(),
                materials_file=self._import_materials_file.text().strip(),
                dielectric_smoothing=self._import_smoothing.isChecked(),
                notes=self._import_notes.toPlainText(),
                tags=parse_tags(self._import_tags.text()),
            ),
        )
        self._imports_list.item(row).setText(
            self._import_item_text(project.model.geometry_imports[row])
        )
        self._update_import_preview()
        self.refresh_validation()
        self.model_changed.emit()

    def _apply_antenna_changes(self) -> None:
        row = self._antennas_list.currentRow()
        project = self._model_editor_service.current_project()
        if self._loading or project is None or not (0 <= row < len(project.model.antenna_models)):
            return
        self._model_editor_service.update_antenna_model(
            row,
            AntennaModelDefinition(
                identifier=self._antenna_id.text().strip(),
                library=str(self._antenna_library.currentData() or ""),
                model_key=str(self._antenna_model.currentData() or ""),
                module_path=self._antenna_module.text().strip(),
                function_name=self._antenna_function.text().strip(),
                position_m=Vector3(
                    x=self._antenna_pos_x.value(),
                    y=self._antenna_pos_y.value(),
                    z=self._antenna_pos_z.value(),
                ),
                resolution_m=self._antenna_resolution.value(),
                rotate90=self._antenna_rotate.isChecked(),
                notes=self._antenna_notes.toPlainText(),
                tags=parse_tags(self._antenna_tags.text()),
            ),
        )
        self._antennas_list.item(row).setText(
            self._antenna_item_text(project.model.antenna_models[row])
        )
        self._update_antenna_preview()
        self.refresh_validation()
        self.model_changed.emit()

    def _add_import(self) -> None:
        row = self._model_editor_service.add_geometry_import()
        self.set_project(self._model_editor_service.current_project())
        self._imports_list.setCurrentRow(row)
        self.model_changed.emit()

    def _duplicate_import(self) -> None:
        row = self._imports_list.currentRow()
        if row < 0:
            return
        new_index = self._model_editor_service.duplicate_geometry_import(row)
        self.set_project(self._model_editor_service.current_project())
        self._imports_list.setCurrentRow(new_index)
        self.model_changed.emit()

    def _delete_import(self) -> None:
        row = self._imports_list.currentRow()
        if row < 0:
            return
        next_index = self._model_editor_service.delete_geometry_import(row)
        self.set_project(self._model_editor_service.current_project())
        if next_index is not None:
            self._imports_list.setCurrentRow(next_index)
        self.model_changed.emit()

    def _add_antenna(self) -> None:
        row = self._model_editor_service.add_antenna_model()
        self.set_project(self._model_editor_service.current_project())
        self._antennas_list.setCurrentRow(row)
        self.model_changed.emit()

    def _duplicate_antenna(self) -> None:
        row = self._antennas_list.currentRow()
        if row < 0:
            return
        new_index = self._model_editor_service.duplicate_antenna_model(row)
        self.set_project(self._model_editor_service.current_project())
        self._antennas_list.setCurrentRow(new_index)
        self.model_changed.emit()

    def _delete_antenna(self) -> None:
        row = self._antennas_list.currentRow()
        if row < 0:
            return
        next_index = self._model_editor_service.delete_antenna_model(row)
        self.set_project(self._model_editor_service.current_project())
        if next_index is not None:
            self._antennas_list.setCurrentRow(next_index)
        self.model_changed.emit()

    def _browse_geometry_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._localization.text("editor.libraries.geometry_dialog"),
            "",
            "HDF5 (*.h5 *.hdf5);;All files (*.*)",
        )
        if path:
            self._import_geometry_file.setText(self._normalize_path_for_project(path))

    def _browse_materials_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._localization.text("editor.libraries.materials_dialog"),
            "",
            "Text (*.txt *.in);;All files (*.*)",
        )
        if path:
            self._import_materials_file.setText(self._normalize_path_for_project(path))

    def _import_item_text(self, item: GeometryImportDefinition) -> str:
        return f"{item.identifier or 'import'} | {item.geometry_hdf5 or '-'}"

    def _antenna_item_text(self, item: AntennaModelDefinition) -> str:
        return f"{item.identifier or 'antenna'} | {item.model_key or item.function_name}"

    def _normalize_path_for_project(self, raw_path: str) -> str:
        project = self._model_editor_service.current_project()
        if project is None:
            return raw_path
        path = Path(raw_path)
        try:
            return str(path.resolve().relative_to(project.root.resolve()))
        except Exception:
            return str(path)

    def _resolve_project_path(self, raw_path: str) -> Path | None:
        normalized = raw_path.strip()
        if not normalized or self._model_editor_service.current_project() is None:
            return None
        project_root = self._model_editor_service.current_project().root
        path = Path(normalized)
        if path.is_absolute():
            return path
        return project_root / path

    def _update_import_preview(self) -> None:
        row = self._imports_list.currentRow()
        project = self._model_editor_service.current_project()
        if project is None or row < 0 or row >= len(project.model.geometry_imports):
            self._import_preview_label.setText(
                self._localization.text("editor.libraries.no_import_preview")
            )
            return
        item = project.model.geometry_imports[row]
        geometry_path = self._resolve_project_path(item.geometry_hdf5)
        materials_path = self._resolve_project_path(item.materials_file)
        geometry_state = (
            self._localization.text("editor.libraries.file_exists")
            if geometry_path is not None and geometry_path.exists()
            else self._localization.text("editor.libraries.file_missing")
        )
        materials_state = (
            self._localization.text("editor.libraries.file_exists")
            if materials_path is not None and materials_path.exists()
            else self._localization.text("editor.libraries.file_missing")
        )
        suffix = " y" if item.dielectric_smoothing else ""
        self._import_preview_label.setText(
            self._localization.text(
                "editor.libraries.import_preview",
                geometry_file=item.geometry_hdf5 or "-",
                materials_file=item.materials_file or "-",
                geometry_state=geometry_state,
                materials_state=materials_state,
                command=(
                    f"#geometry_objects_read: {item.position_m.x:.6g} {item.position_m.y:.6g} "
                    f"{item.position_m.z:.6g} {item.geometry_hdf5 or '<geometry>'} "
                    f"{item.materials_file or '<materials>'}{suffix}"
                ),
            )
        )

    def _update_antenna_preview(self) -> None:
        row = self._antennas_list.currentRow()
        project = self._model_editor_service.current_project()
        if project is None or row < 0 or row >= len(project.model.antenna_models):
            self._antenna_catalog_summary.setText(
                self._localization.text("editor.libraries.no_catalog_preview")
            )
            self._antenna_preview_label.setText(
                self._localization.text("editor.libraries.no_antenna_preview")
            )
            return
        antenna = project.model.antenna_models[row]
        catalog = antenna_catalog_entry(antenna.library, antenna.model_key)
        if catalog is None:
            self._antenna_catalog_summary.setText(
                self._localization.text("editor.libraries.catalog_custom")
            )
        else:
            supported = catalog.get("supported_resolutions_m", ())
            supported_text = ", ".join(f"{value:.4g}" for value in supported) if isinstance(supported, tuple) else "-"
            self._antenna_catalog_summary.setText(
                self._localization.text(
                    "editor.libraries.catalog_summary",
                    label=str(catalog.get("label", antenna.model_key)),
                    manufacturer=str(catalog.get("manufacturer", antenna.library)),
                    description=str(catalog.get("description", "")),
                    dimensions=str(catalog.get("dimensions_mm", "-")),
                    resolutions=supported_text,
                )
            )
        rotation = ", rotate90=True" if antenna.rotate90 else ""
        self._antenna_preview_label.setText(
            self._localization.text(
                "editor.libraries.antenna_preview",
                module=antenna.module_path or "<module>",
                function=antenna.function_name or "<function>",
                x=f"{antenna.position_m.x:.6g}",
                y=f"{antenna.position_m.y:.6g}",
                z=f"{antenna.position_m.z:.6g}",
                resolution=f"{antenna.resolution_m:.6g}",
                rotation=rotation,
            )
        )
