from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...application.services.input_preview_service import InputPreviewService
from ...application.services.model_editor_service import ModelEditorService
from ...application.services.validation_service import ValidationService
from ...domain.models import Project
from ...domain.validation import ValidationResult
from ..widgets.model_editor.general_panel import GeneralPanel
from ..widgets.model_editor.geometry_panel import GeometryPanel
from ..widgets.model_editor.materials_panel import MaterialsPanel
from ..widgets.model_editor.preview_panel import PreviewPanel
from ..widgets.model_editor.receivers_panel import ReceiversPanel
from ..widgets.model_editor.sources_panel import SourcesPanel
from ..widgets.model_editor.waveforms_panel import WaveformsPanel


class ProjectView(QWidget):
    save_requested = Signal()
    editor_changed = Signal()

    def __init__(
        self,
        *,
        model_editor_service: ModelEditorService,
        validation_service: ValidationService,
        input_preview_service: InputPreviewService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model_editor_service = model_editor_service
        self._validation_service = validation_service
        self._project_file: str | None = None
        self._is_dirty = False

        self._project_root_label = QLabel("No project open")
        self._project_file_label = QLabel("Manifest: -")
        self._summary_label = QLabel(
            "Open or create a project to edit gprMax model entities."
        )
        self._summary_label.setWordWrap(True)
        self._validation_label = QLabel("Validation: no project loaded.")
        self._validation_label.setWordWrap(True)

        self._save_button = QPushButton("Save Project")
        self._save_button.clicked.connect(self.save_requested.emit)

        self._general_panel = GeneralPanel(model_editor_service, validation_service)
        self._materials_panel = MaterialsPanel(model_editor_service, validation_service)
        self._waveforms_panel = WaveformsPanel(model_editor_service, validation_service)
        self._sources_panel = SourcesPanel(model_editor_service, validation_service)
        self._receivers_panel = ReceiversPanel(model_editor_service, validation_service)
        self._geometry_panel = GeometryPanel(model_editor_service, validation_service)
        self._preview_panel = PreviewPanel(model_editor_service, input_preview_service)

        for panel in (
            self._general_panel,
            self._materials_panel,
            self._waveforms_panel,
            self._sources_panel,
            self._receivers_panel,
            self._geometry_panel,
        ):
            panel.model_changed.connect(self._on_model_changed)

        header = QLabel("Model Editor")
        header.setObjectName("ViewTitle")
        subtitle = QLabel(
            "Stage 4 provides a form-based editor for the practical gprMax MVP subset: essential model settings, materials, waveforms, sources, receivers, geometry, and input preview."
        )
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        project_card = QFrame()
        project_card.setObjectName("ViewCard")
        project_layout = QVBoxLayout(project_card)
        project_layout.setContentsMargins(20, 18, 20, 18)
        project_layout.setSpacing(8)
        project_layout.addWidget(QLabel("Project workspace"))
        project_layout.addWidget(self._project_root_label)
        project_layout.addWidget(self._project_file_label)
        project_layout.addWidget(self._summary_label)
        project_layout.addWidget(self._validation_label)

        card_actions = QHBoxLayout()
        card_actions.addWidget(self._save_button)
        card_actions.addStretch(1)
        project_layout.addLayout(card_actions)

        tabs = QTabWidget()
        tabs.addTab(self._general_panel, "General")
        tabs.addTab(self._materials_panel, "Materials")
        tabs.addTab(self._waveforms_panel, "Waveforms")
        tabs.addTab(self._sources_panel, "Sources")
        tabs.addTab(self._receivers_panel, "Receivers")
        tabs.addTab(self._geometry_panel, "Geometry")
        tabs.addTab(self._preview_panel, "Input Preview")
        self._tabs = tabs

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addWidget(project_card)
        layout.addWidget(tabs, 1)

        self.set_project(None, None, False, None)

    def set_project(
        self,
        project: Project | None,
        validation: ValidationResult | None,
        is_dirty: bool,
        project_file: str | None,
    ) -> None:
        self._project_file = project_file
        self._is_dirty = is_dirty
        self._save_button.setEnabled(project is not None)
        self._project_root_label.setText(str(project.root) if project else "No project open")
        self._project_file_label.setText(f"Manifest: {project_file or '-'}")

        if project is None:
            self._summary_label.setText(
                "Open or create a project to edit gprMax model entities."
            )
            self._validation_label.setText("Validation: no project loaded.")
            self._preview_panel.clear()
        else:
            self._summary_label.setText(
                f"Editing '{project.metadata.name}'. "
                f"Materials: {len(project.model.materials)}, "
                f"Geometry: {len(project.model.geometry)}, "
                f"Sources: {len(project.model.sources)}, "
                f"Receivers: {len(project.model.receivers)}."
            )
            self._validation_label.setText(self._format_validation(validation, is_dirty))

        self._general_panel.set_project(project)
        self._materials_panel.set_project(project)
        self._waveforms_panel.set_project(project)
        self._sources_panel.set_project(project)
        self._receivers_panel.set_project(project)
        self._geometry_panel.set_project(project)

    def _on_model_changed(self) -> None:
        project = self._model_editor_service.current_project()
        validation = self._validation_service.current_validation()
        self._is_dirty = True

        self._general_panel.refresh_validation()
        self._materials_panel.refresh_validation()
        self._waveforms_panel.refresh_validation()
        self._sources_panel.refresh_waveform_choices()
        self._sources_panel.refresh_validation()
        self._receivers_panel.refresh_validation()
        self._geometry_panel.refresh_material_choices()
        self._geometry_panel.refresh_validation()

        if project is None:
            self._summary_label.setText("Open or create a project to edit gprMax model entities.")
            self._validation_label.setText("Validation: no project loaded.")
        else:
            self._summary_label.setText(
                f"Editing '{project.metadata.name}'. "
                f"Materials: {len(project.model.materials)}, "
                f"Geometry: {len(project.model.geometry)}, "
                f"Sources: {len(project.model.sources)}, "
                f"Receivers: {len(project.model.receivers)}."
            )
            self._validation_label.setText(self._format_validation(validation, True))

        self.editor_changed.emit()

    def _format_validation(
        self,
        validation: ValidationResult | None,
        is_dirty: bool,
    ) -> str:
        if validation is None:
            return "Validation: no issues."

        state = "Unsaved changes." if is_dirty else "Saved."
        if not validation.issues:
            return f"{state} Validation: no issues."

        return (
            f"{state} Validation: {len(validation.errors)} error(s), "
            f"{len(validation.warnings)} warning(s)."
        )
