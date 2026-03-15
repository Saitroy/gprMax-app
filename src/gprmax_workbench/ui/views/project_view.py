from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...application.services.project_service import ProjectDraft
from ...domain.models import Project, Vector3
from ...domain.validation import ValidationResult


class ProjectView(QWidget):
    save_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._project_root_label = QLabel("No project open")
        self._project_file_label = QLabel("Manifest: -")
        self._status_label = QLabel(
            "Open or create a project to edit essential model settings."
        )
        self._status_label.setWordWrap(True)

        self._name_edit = QLineEdit()
        self._description_edit = QPlainTextEdit()
        self._description_edit.setFixedHeight(80)
        self._title_edit = QLineEdit()

        self._size_x = self._build_float_spinbox()
        self._size_y = self._build_float_spinbox()
        self._size_z = self._build_float_spinbox()
        self._resolution_x = self._build_float_spinbox()
        self._resolution_y = self._build_float_spinbox()
        self._resolution_z = self._build_float_spinbox()
        self._time_window = self._build_float_spinbox(decimals=12, maximum=1.0)

        self._save_button = QPushButton("Save Project")
        self._save_button.clicked.connect(self.save_requested.emit)

        metadata_group = self._build_metadata_group()
        domain_group = self._build_domain_group()

        header = QLabel("Model Editor")
        header.setObjectName("ViewTitle")

        subtitle = QLabel(
            "Stage 2 exposes only the essential project metadata and the core gprMax "
            "domain settings aligned with the documentation's essential commands."
        )
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        top_card = QFrame()
        top_card.setObjectName("ViewCard")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(20, 18, 20, 18)
        top_layout.setSpacing(8)
        project_location_label = QLabel("Project location")
        project_location_label.setObjectName("SectionTitle")
        top_layout.addWidget(project_location_label)
        top_layout.addWidget(self._project_root_label)
        top_layout.addWidget(self._project_file_label)
        top_layout.addWidget(self._status_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addWidget(top_card)
        layout.addWidget(metadata_group)
        layout.addWidget(domain_group)
        layout.addWidget(self._save_button)
        layout.addStretch(1)

        self.set_project(None, None, False, None)

    def collect_draft(self) -> ProjectDraft:
        return ProjectDraft(
            project_name=self._name_edit.text(),
            description=self._description_edit.toPlainText(),
            model_title=self._title_edit.text(),
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

    def set_project(
        self,
        project: Project | None,
        validation: ValidationResult | None,
        is_dirty: bool,
        project_file: str | None,
    ) -> None:
        enabled = project is not None
        for widget in (
            self._name_edit,
            self._description_edit,
            self._title_edit,
            self._size_x,
            self._size_y,
            self._size_z,
            self._resolution_x,
            self._resolution_y,
            self._resolution_z,
            self._time_window,
        ):
            widget.setEnabled(enabled)
        self._save_button.setEnabled(enabled)

        if project is None:
            self._project_root_label.setText("No project open")
            self._project_file_label.setText("Manifest: -")
            self._status_label.setText(
                "Open or create a project to edit essential model settings."
            )
            self._name_edit.clear()
            self._description_edit.clear()
            self._title_edit.clear()
            self._set_spinboxes_defaults()
            return

        self._project_root_label.setText(str(project.root))
        self._project_file_label.setText(f"Manifest: {project_file or '-'}")
        self._name_edit.setText(project.metadata.name)
        self._description_edit.setPlainText(project.metadata.description)
        self._title_edit.setText(project.model.title)

        self._size_x.setValue(project.model.domain.size_m.x)
        self._size_y.setValue(project.model.domain.size_m.y)
        self._size_z.setValue(project.model.domain.size_m.z)
        self._resolution_x.setValue(project.model.domain.resolution_m.x)
        self._resolution_y.setValue(project.model.domain.resolution_m.y)
        self._resolution_z.setValue(project.model.domain.resolution_m.z)
        self._time_window.setValue(project.model.domain.time_window_s)

        issues_text = self._format_validation(validation)
        dirty_marker = "Unsaved changes." if is_dirty else "Saved."
        self._status_label.setText(f"{dirty_marker} {issues_text}")

    def _build_metadata_group(self) -> QGroupBox:
        group = QGroupBox("Project metadata")
        group.setObjectName("ViewCard")
        layout = QFormLayout(group)
        layout.addRow("Project name", self._name_edit)
        layout.addRow("Description", self._description_edit)
        layout.addRow("gprMax title", self._title_edit)
        return group

    def _build_domain_group(self) -> QGroupBox:
        group = QGroupBox("Essential domain settings")
        layout = QGridLayout(group)

        layout.addWidget(QLabel("Domain size (m)"), 0, 0)
        layout.addWidget(self._size_x, 0, 1)
        layout.addWidget(self._size_y, 0, 2)
        layout.addWidget(self._size_z, 0, 3)

        layout.addWidget(QLabel("Resolution (m)"), 1, 0)
        layout.addWidget(self._resolution_x, 1, 1)
        layout.addWidget(self._resolution_y, 1, 2)
        layout.addWidget(self._resolution_z, 1, 3)

        layout.addWidget(QLabel("Time window (s)"), 2, 0)
        layout.addWidget(self._time_window, 2, 1)

        axes_row = QHBoxLayout()
        for label in ("X", "Y", "Z"):
            axis_label = QLabel(label)
            axes_row.addWidget(axis_label)
        axes_row.addStretch(1)

        layout.addLayout(axes_row, 3, 0, 1, 4)
        return group

    def _build_float_spinbox(
        self,
        *,
        decimals: int = 6,
        maximum: float = 1_000_000.0,
    ) -> QDoubleSpinBox:
        spinbox = QDoubleSpinBox()
        spinbox.setDecimals(decimals)
        spinbox.setRange(0.0, maximum)
        spinbox.setSingleStep(0.001)
        return spinbox

    def _format_validation(self, validation: ValidationResult | None) -> str:
        if validation is None or not validation.issues:
            return "No validation issues."

        parts = []
        if validation.errors:
            parts.append(f"Errors: {len(validation.errors)}")
        if validation.warnings:
            parts.append(f"Warnings: {len(validation.warnings)}")
        return ", ".join(parts)

    def _set_spinboxes_defaults(self) -> None:
        for spinbox, value in (
            (self._size_x, 1.0),
            (self._size_y, 1.0),
            (self._size_z, 0.1),
            (self._resolution_x, 0.01),
            (self._resolution_y, 0.01),
            (self._resolution_z, 0.01),
            (self._time_window, 3e-9),
        ):
            spinbox.setValue(value)
