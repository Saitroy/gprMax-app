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
from ...application.services.localization_service import LocalizationService
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
        localization: LocalizationService,
        model_editor_service: ModelEditorService,
        validation_service: ValidationService,
        input_preview_service: InputPreviewService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._model_editor_service = model_editor_service
        self._validation_service = validation_service
        self._project_file: str | None = None
        self._is_dirty = False
        self._current_project: Project | None = None

        self._project_root_label = QLabel()
        self._project_file_label = QLabel()
        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)
        self._validation_label = QLabel()
        self._validation_label.setWordWrap(True)

        self._save_button = QPushButton()
        self._save_button.clicked.connect(self.save_requested.emit)

        self._general_panel = GeneralPanel(localization, model_editor_service, validation_service)
        self._materials_panel = MaterialsPanel(localization, model_editor_service, validation_service)
        self._waveforms_panel = WaveformsPanel(localization, model_editor_service, validation_service)
        self._sources_panel = SourcesPanel(localization, model_editor_service, validation_service)
        self._receivers_panel = ReceiversPanel(localization, model_editor_service, validation_service)
        self._geometry_panel = GeometryPanel(localization, model_editor_service, validation_service)
        self._preview_panel = PreviewPanel(localization, model_editor_service, input_preview_service)

        for panel in (
            self._general_panel,
            self._materials_panel,
            self._waveforms_panel,
            self._sources_panel,
            self._receivers_panel,
            self._geometry_panel,
        ):
            panel.model_changed.connect(self._on_model_changed)

        self._header = QLabel()
        self._header.setObjectName("ViewTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        project_card = QFrame()
        project_card.setObjectName("ViewCard")
        project_layout = QVBoxLayout(project_card)
        project_layout.setContentsMargins(20, 18, 20, 18)
        project_layout.setSpacing(8)
        self._project_workspace_label = QLabel()
        project_layout.addWidget(self._project_workspace_label)
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
        layout.addWidget(self._header)
        layout.addWidget(self._subtitle)
        layout.addWidget(project_card)
        layout.addWidget(tabs, 1)

        self.retranslate_ui()
        self.set_project(None, None, False, None)

    def set_project(
        self,
        project: Project | None,
        validation: ValidationResult | None,
        is_dirty: bool,
        project_file: str | None,
    ) -> None:
        self._current_project = project
        self._project_file = project_file
        self._is_dirty = is_dirty
        self._save_button.setEnabled(project is not None)
        self._project_root_label.setText(
            str(project.root) if project else self._localization.text("project.no_project")
        )
        self._project_file_label.setText(
            self._localization.text("project.manifest", path=project_file or "-")
        )

        if project is None:
            self._summary_label.setText(self._localization.text("project.summary.empty"))
            self._validation_label.setText(self._localization.text("project.validation.empty"))
            self._preview_panel.clear()
        else:
            self._summary_label.setText(
                self._localization.text(
                    "project.summary.editing",
                    name=project.metadata.name,
                    materials=len(project.model.materials),
                    geometry=len(project.model.geometry),
                    sources=len(project.model.sources),
                    receivers=len(project.model.receivers),
                )
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
            self._summary_label.setText(self._localization.text("project.summary.empty"))
            self._validation_label.setText(self._localization.text("project.validation.empty"))
        else:
            self._summary_label.setText(
                self._localization.text(
                    "project.summary.editing",
                    name=project.metadata.name,
                    materials=len(project.model.materials),
                    geometry=len(project.model.geometry),
                    sources=len(project.model.sources),
                    receivers=len(project.model.receivers),
                )
            )
            self._validation_label.setText(self._format_validation(validation, True))

        self.editor_changed.emit()

    def _format_validation(
        self,
        validation: ValidationResult | None,
        is_dirty: bool,
    ) -> str:
        if validation is None:
            return self._localization.text("project.validation.clean", state="")

        state = self._localization.text(
            "project.state.unsaved" if is_dirty else "project.state.saved"
        )
        if not validation.issues:
            return self._localization.text("project.validation.clean", state=state)

        return self._localization.text(
            "project.validation.summary",
            state=state,
            errors=len(validation.errors),
            warnings=len(validation.warnings),
        )

    def retranslate_ui(self) -> None:
        self._header.setText(self._localization.text("project.title"))
        self._subtitle.setText(self._localization.text("project.subtitle"))
        self._project_workspace_label.setText(self._localization.text("project.workspace"))
        self._save_button.setText(self._localization.text("action.save_project"))
        self._tabs.setTabText(0, self._localization.text("project.tab.general"))
        self._tabs.setTabText(1, self._localization.text("project.tab.materials"))
        self._tabs.setTabText(2, self._localization.text("project.tab.waveforms"))
        self._tabs.setTabText(3, self._localization.text("project.tab.sources"))
        self._tabs.setTabText(4, self._localization.text("project.tab.receivers"))
        self._tabs.setTabText(5, self._localization.text("project.tab.geometry"))
        self._tabs.setTabText(6, self._localization.text("project.tab.preview"))
        self._general_panel.retranslate_ui()
        self._materials_panel.retranslate_ui()
        self._waveforms_panel.retranslate_ui()
        self._sources_panel.retranslate_ui()
        self._receivers_panel.retranslate_ui()
        self._geometry_panel.retranslate_ui()
        self._preview_panel.retranslate_ui()
        self.set_project(self._current_project, self._validation_service.current_validation(), self._is_dirty, self._project_file)
