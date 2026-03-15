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
    QVBoxLayout,
    QWidget,
)

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
        model_editor_service: ModelEditorService,
        validation_service: ValidationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model_editor_service = model_editor_service
        self._validation_service = validation_service
        self._loading = False

        self._project_name_edit = QLineEdit()
        self._description_edit = QPlainTextEdit()
        self._description_edit.setFixedHeight(80)
        self._model_title_edit = QLineEdit()
        self._model_notes_edit = QPlainTextEdit()
        self._model_notes_edit.setFixedHeight(100)
        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("Comma-separated tags")

        self._size_x = build_float_spinbox()
        self._size_y = build_float_spinbox()
        self._size_z = build_float_spinbox()
        self._resolution_x = build_float_spinbox(decimals=6, step=0.0001)
        self._resolution_y = build_float_spinbox(decimals=6, step=0.0001)
        self._resolution_z = build_float_spinbox(decimals=6, step=0.0001)
        self._time_window = build_float_spinbox(decimals=12, maximum=1.0, step=1e-10)
        self._status_label = build_status_label(
            "General settings validation will appear here."
        )

        metadata_group = QGroupBox("Project and model")
        metadata_layout = QFormLayout(metadata_group)
        metadata_layout.addRow("Project name", self._project_name_edit)
        metadata_layout.addRow("Description", self._description_edit)
        metadata_layout.addRow("Model title", self._model_title_edit)
        metadata_layout.addRow("Model notes", self._model_notes_edit)
        metadata_layout.addRow("Tags", self._tags_edit)

        domain_group = QGroupBox("Essential gprMax setup")
        domain_layout = QGridLayout(domain_group)
        domain_layout.addWidget(QLabel("Domain size (m)"), 0, 0)
        domain_layout.addWidget(self._size_x, 0, 1)
        domain_layout.addWidget(self._size_y, 0, 2)
        domain_layout.addWidget(self._size_z, 0, 3)
        domain_layout.addWidget(QLabel("Resolution (m)"), 1, 0)
        domain_layout.addWidget(self._resolution_x, 1, 1)
        domain_layout.addWidget(self._resolution_y, 1, 2)
        domain_layout.addWidget(self._resolution_z, 1, 3)
        domain_layout.addWidget(QLabel("Time window (s)"), 2, 0)
        domain_layout.addWidget(self._time_window, 2, 1)

        axis_hint = QHBoxLayout()
        axis_hint.addWidget(QLabel("X"))
        axis_hint.addWidget(QLabel("Y"))
        axis_hint.addWidget(QLabel("Z"))
        axis_hint.addStretch(1)
        domain_layout.addLayout(axis_hint, 3, 1, 1, 3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(metadata_group)
        layout.addWidget(domain_group)
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
        ):
            widget.valueChanged.connect(self._apply_changes)

        self.set_project(None)

    def set_project(self, project: Project | None) -> None:
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
            self._status_label.setText(
                "Open or create a project to edit general settings."
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
        self._loading = False
        self.refresh_validation()

    def refresh_validation(self) -> None:
        messages = self._validation_service.messages_for_prefixes(
            "metadata",
            "model.title",
            "model.domain",
        )
        self._status_label.setText(
            join_messages(messages, "General settings look consistent.")
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
        )
        self.refresh_validation()
        self.model_changed.emit()
