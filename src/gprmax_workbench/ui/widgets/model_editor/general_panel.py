from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.models import Project, Vector3
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_tags,
    tags_to_text,
)


class GeneralPanel(QWidget):
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
        self._current_project: Project | None = None

        self._project_name_edit = QLineEdit()
        self._description_edit = QPlainTextEdit()
        self._description_edit.setFixedHeight(80)
        self._model_title_edit = QLineEdit()
        self._model_notes_edit = QPlainTextEdit()
        self._model_notes_edit.setFixedHeight(100)
        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("")

        self._size_x = build_float_spinbox()
        self._size_y = build_float_spinbox()
        self._size_z = build_float_spinbox()
        self._resolution_x = build_float_spinbox(decimals=6, step=0.0001)
        self._resolution_y = build_float_spinbox(decimals=6, step=0.0001)
        self._resolution_z = build_float_spinbox(decimals=6, step=0.0001)
        self._time_window = build_float_spinbox(decimals=12, maximum=1.0, step=1e-10)
        self._scan_trace_count = QSpinBox()
        self._scan_trace_count.setRange(0, 1_000_000)
        self._scan_trace_count.setSpecialValueText("")
        self._status_label = build_status_label("")

        self._metadata_group = QGroupBox()
        metadata_layout = QFormLayout(self._metadata_group)
        self._project_name_label = QLabel()
        self._description_label = QLabel()
        self._model_title_label = QLabel()
        self._model_notes_label = QLabel()
        self._tags_label = QLabel()
        metadata_layout.addRow(self._project_name_label, self._project_name_edit)
        metadata_layout.addRow(self._description_label, self._description_edit)
        metadata_layout.addRow(self._model_title_label, self._model_title_edit)
        metadata_layout.addRow(self._model_notes_label, self._model_notes_edit)
        metadata_layout.addRow(self._tags_label, self._tags_edit)

        self._domain_group = QGroupBox()
        domain_layout = QGridLayout(self._domain_group)
        self._domain_size_label = QLabel()
        self._resolution_label = QLabel()
        self._time_window_label = QLabel()
        self._scan_trace_count_label = QLabel()
        domain_layout.addWidget(self._domain_size_label, 0, 0)
        domain_layout.addWidget(self._size_x, 0, 1)
        domain_layout.addWidget(self._size_y, 0, 2)
        domain_layout.addWidget(self._size_z, 0, 3)
        domain_layout.addWidget(self._resolution_label, 1, 0)
        domain_layout.addWidget(self._resolution_x, 1, 1)
        domain_layout.addWidget(self._resolution_y, 1, 2)
        domain_layout.addWidget(self._resolution_z, 1, 3)
        domain_layout.addWidget(self._time_window_label, 2, 0)
        domain_layout.addWidget(self._time_window, 2, 1)
        domain_layout.addWidget(self._scan_trace_count_label, 3, 0)
        domain_layout.addWidget(self._scan_trace_count, 3, 1)

        axis_hint = QHBoxLayout()
        axis_hint.addWidget(QLabel("X"))
        axis_hint.addWidget(QLabel("Y"))
        axis_hint.addWidget(QLabel("Z"))
        axis_hint.addStretch(1)
        domain_layout.addLayout(axis_hint, 4, 1, 1, 3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._metadata_group)
        layout.addWidget(self._domain_group)
        layout.addWidget(self._status_label)
        layout.addStretch(1)

        for widget in (
            self._project_name_edit,
            self._model_title_edit,
            self._tags_edit,
        ):
            widget.textChanged.connect(self._apply_changes)
        for widget in (self._description_edit, self._model_notes_edit):
            widget.textChanged.connect(self._apply_changes)
        for widget in (
            self._size_x,
            self._size_y,
            self._size_z,
            self._resolution_x,
            self._resolution_y,
            self._resolution_z,
            self._time_window,
            self._scan_trace_count,
        ):
            widget.valueChanged.connect(self._apply_changes)

        self.retranslate_ui()
        self.set_project(None)

    def set_project(self, project: Project | None) -> None:
        self._current_project = project
        self._loading = True
        enabled = project is not None
        for widget in (
            self._project_name_edit,
            self._description_edit,
            self._model_title_edit,
            self._model_notes_edit,
            self._tags_edit,
            self._size_x,
            self._size_y,
            self._size_z,
            self._resolution_x,
            self._resolution_y,
            self._resolution_z,
            self._time_window,
            self._scan_trace_count,
        ):
            widget.setEnabled(enabled)

        if project is None:
            self._project_name_edit.clear()
            self._description_edit.clear()
            self._model_title_edit.clear()
            self._model_notes_edit.clear()
            self._tags_edit.clear()
            self._size_x.setValue(1.0)
            self._size_y.setValue(1.0)
            self._size_z.setValue(0.1)
            self._resolution_x.setValue(0.01)
            self._resolution_y.setValue(0.01)
            self._resolution_z.setValue(0.01)
            self._time_window.setValue(3e-9)
            self._scan_trace_count.setValue(0)
            self._status_label.setText(
                self._localization.text("editor.general.open_project")
            )
            self._loading = False
            return

        self._project_name_edit.setText(project.metadata.name)
        self._description_edit.setPlainText(project.metadata.description)
        self._model_title_edit.setText(project.model.title)
        self._model_notes_edit.setPlainText(project.model.notes)
        self._tags_edit.setText(tags_to_text(project.model.tags))
        self._size_x.setValue(project.model.domain.size_m.x)
        self._size_y.setValue(project.model.domain.size_m.y)
        self._size_z.setValue(project.model.domain.size_m.z)
        self._resolution_x.setValue(project.model.domain.resolution_m.x)
        self._resolution_y.setValue(project.model.domain.resolution_m.y)
        self._resolution_z.setValue(project.model.domain.resolution_m.z)
        self._time_window.setValue(project.model.domain.time_window_s)
        self._scan_trace_count.setValue(project.model.scan_trace_count or 0)
        self._loading = False
        self.refresh_validation()

    def refresh_validation(self) -> None:
        messages = self._validation_service.messages_for_prefixes(
            "metadata",
            "model.title",
            "model.domain",
            "model.scan_trace_count",
        )
        self._status_label.setText(
            join_messages(messages, self._localization.text("editor.general.valid"))
        )

    def _apply_changes(self) -> None:
        if self._loading or self._model_editor_service.current_project() is None:
            return

        self._model_editor_service.update_project_overview(
            project_name=self._project_name_edit.text(),
            description=self._description_edit.toPlainText(),
            model_title=self._model_title_edit.text(),
            model_notes=self._model_notes_edit.toPlainText(),
            model_tags=parse_tags(self._tags_edit.text()),
            domain_size_m=Vector3(
                x=self._size_x.value(),
                y=self._size_y.value(),
                z=self._size_z.value(),
            ),
            resolution_m=Vector3(
                x=self._resolution_x.value(),
                y=self._resolution_y.value(),
                z=self._resolution_z.value(),
            ),
            time_window_s=self._time_window.value(),
            scan_trace_count=self._scan_trace_count.value() or None,
        )
        self.refresh_validation()
        self.model_changed.emit()

    def retranslate_ui(self) -> None:
        self._tags_edit.setPlaceholderText(
            self._localization.text("editor.general.tags_placeholder")
        )
        self._metadata_group.setTitle(
            self._localization.text("editor.general.metadata_group")
        )
        self._project_name_label.setText(
            self._localization.text("editor.general.project_name")
        )
        self._description_label.setText(
            self._localization.text("editor.general.description")
        )
        self._model_title_label.setText(
            self._localization.text("editor.general.model_title")
        )
        self._model_notes_label.setText(
            self._localization.text("editor.general.model_notes")
        )
        self._tags_label.setText(self._localization.text("editor.general.tags"))
        self._domain_group.setTitle(
            self._localization.text("editor.general.domain_group")
        )
        self._domain_size_label.setText(
            self._localization.text("editor.general.domain_size")
        )
        self._resolution_label.setText(
            self._localization.text("editor.general.resolution")
        )
        self._time_window_label.setText(
            self._localization.text("editor.general.time_window")
        )
        self._scan_trace_count_label.setText(
            self._localization.text("editor.general.scan_trace_count")
        )
        self._scan_trace_count.setSpecialValueText(
            self._localization.text("editor.general.scan_trace_count_auto")
        )
        if self._current_project is None:
            self._status_label.setText(
                self._localization.text("editor.general.open_project")
            )
        else:
            self.refresh_validation()
