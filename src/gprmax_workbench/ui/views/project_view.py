from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ...application.services.input_preview_service import InputPreviewService
from ...application.services.localization_service import LocalizationService
from ...application.services.model_editor_service import ModelEditorService
from ...application.services.validation_service import ValidationService
from ...domain.models import Project
from ...domain.validation import ValidationResult
from ...infrastructure.gprmax.command_registry import GprMaxCommandRegistry
from ..splitters import configure_splitter
from ..widgets.model_editor.advanced_panel import AdvancedPanel
from ..widgets.model_editor.general_panel import GeneralPanel
from ..widgets.model_editor.geometry_panel import GeometryPanel
from ..widgets.model_editor.libraries_panel import LibrariesPanel
from ..widgets.model_editor.materials_panel import MaterialsPanel
from ..widgets.model_editor.preview_panel import PreviewPanel
from ..widgets.model_editor.receivers_panel import ReceiversPanel
from ..widgets.model_editor.scene_canvas_panel import SceneCanvasPanel
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
        command_registry: GprMaxCommandRegistry,
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
        self._workflow_hint = QLabel()
        self._workflow_hint.setObjectName("SectionBody")
        self._workflow_hint.setWordWrap(True)
        self._section_nav = QListWidget()
        self._section_nav.setObjectName("ContextNavigation")
        self._section_nav.currentRowChanged.connect(self._on_section_changed)
        self._section_stack = QStackedWidget()

        self._save_button = QPushButton()
        self._save_button.clicked.connect(self.save_requested.emit)

        self._general_panel = GeneralPanel(localization, model_editor_service, validation_service)
        self._materials_panel = MaterialsPanel(localization, model_editor_service, validation_service)
        self._waveforms_panel = WaveformsPanel(localization, model_editor_service, validation_service)
        self._sources_panel = SourcesPanel(localization, model_editor_service, validation_service)
        self._receivers_panel = ReceiversPanel(localization, model_editor_service, validation_service)
        self._geometry_panel = GeometryPanel(localization, model_editor_service, validation_service)
        self._scene_panel = SceneCanvasPanel(localization, model_editor_service, validation_service)
        self._libraries_panel = LibrariesPanel(localization, model_editor_service, validation_service)
        self._advanced_panel = AdvancedPanel(
            localization,
            model_editor_service,
            validation_service,
            command_registry,
        )
        self._preview_panel = PreviewPanel(localization, model_editor_service, input_preview_service)
        self._sections: list[tuple[str, QWidget]] = [
            ("project.section.scene", self._scene_panel),
            ("project.section.area", self._general_panel),
            ("project.section.materials", self._materials_panel),
            ("project.section.signal", self._waveforms_panel),
            ("project.section.sources", self._sources_panel),
            ("project.section.receivers", self._receivers_panel),
            ("project.section.geometry", self._geometry_panel),
            ("project.section.libraries", self._libraries_panel),
            ("project.section.advanced", self._advanced_panel),
            ("project.section.preview", self._preview_panel),
        ]

        for panel in (
            self._general_panel,
            self._materials_panel,
            self._waveforms_panel,
            self._sources_panel,
            self._receivers_panel,
            self._geometry_panel,
            self._scene_panel,
            self._libraries_panel,
            self._advanced_panel,
        ):
            panel.model_changed.connect(self._on_model_changed)
        self._scene_panel.edit_requested.connect(self._on_scene_edit_requested)

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
        project_layout.addWidget(self._project_root_label)
        project_layout.addWidget(self._project_file_label)
        project_layout.addWidget(self._summary_label)
        project_layout.addWidget(self._validation_label)
        project_layout.addWidget(self._workflow_hint)

        card_actions = QHBoxLayout()
        card_actions.addWidget(self._save_button)
        card_actions.addStretch(1)
        project_layout.addLayout(card_actions)

        nav_card = QFrame()
        nav_card.setObjectName("ViewCard")
        nav_layout = QVBoxLayout(nav_card)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(10)
        self._nav_heading = QLabel()
        self._nav_heading.setObjectName("SectionTitle")
        nav_layout.addWidget(self._nav_heading)
        nav_layout.addWidget(self._section_nav, 1)

        for _, panel in self._sections:
            self._section_stack.addWidget(panel)

        self._content_splitter = configure_splitter(QSplitter())
        self._content_splitter.addWidget(nav_card)
        self._content_splitter.addWidget(self._section_stack)
        self._content_splitter.setStretchFactor(0, 0)
        self._content_splitter.setStretchFactor(1, 1)
        self._content_splitter.setSizes([230, 980])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._header)
        layout.addWidget(self._subtitle)
        layout.addWidget(project_card)
        layout.addWidget(self._content_splitter, 1)

        self.retranslate_ui()
        self._section_nav.setCurrentRow(0)
        self.set_project(None, None, False, None)
        self._refresh_responsive_layout()

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
            self._workflow_hint.setText(self._localization.text("project.workflow_hint.empty"))
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
            self._workflow_hint.setText(self._localization.text("project.workflow_hint"))
        self._general_panel.set_project(project)
        self._materials_panel.set_project(project)
        self._waveforms_panel.set_project(project)
        self._sources_panel.set_project(project)
        self._receivers_panel.set_project(project)
        self._geometry_panel.set_project(project)
        self._scene_panel.set_project(project)
        self._libraries_panel.set_project(project)
        self._advanced_panel.set_project(project)

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
        self._scene_panel.set_project(project)
        self._libraries_panel.set_project(project)
        self._advanced_panel.refresh_validation()

        if project is None:
            self._summary_label.setText(self._localization.text("project.summary.empty"))
            self._validation_label.setText(self._localization.text("project.validation.empty"))
            self._workflow_hint.setText(self._localization.text("project.workflow_hint.empty"))
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
            self._workflow_hint.setText(self._localization.text("project.workflow_hint"))

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
        self._save_button.setText(self._localization.text("action.save_project"))
        self._nav_heading.setText(self._localization.text("project.navigation"))
        self._retranslate_sections()
        self._general_panel.retranslate_ui()
        self._materials_panel.retranslate_ui()
        self._waveforms_panel.retranslate_ui()
        self._sources_panel.retranslate_ui()
        self._receivers_panel.retranslate_ui()
        self._geometry_panel.retranslate_ui()
        self._scene_panel.retranslate_ui()
        self._libraries_panel.retranslate_ui()
        self._advanced_panel.retranslate_ui()
        self._preview_panel.retranslate_ui()
        self.set_project(self._current_project, self._validation_service.current_validation(), self._is_dirty, self._project_file)
        self._refresh_responsive_layout()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_responsive_layout()

    def _retranslate_sections(self) -> None:
        current_row = self._section_nav.currentRow()
        self._section_nav.clear()
        for index, (title_key, _) in enumerate(self._sections):
            item = QListWidgetItem(self._localization.text(title_key))
            item.setData(Qt.ItemDataRole.UserRole, index)
            self._section_nav.addItem(item)
        if self._section_nav.count() > 0:
            self._section_nav.setCurrentRow(max(0, current_row))

    def _on_section_changed(self, row: int) -> None:
        if row < 0:
            return
        self._section_stack.setCurrentIndex(row)

    def _refresh_responsive_layout(self) -> None:
        if self.width() < 980:
            self._content_splitter.setOrientation(Qt.Orientation.Vertical)
            top_height = 176 if self.height() >= 700 else 152
            self._content_splitter.setSizes(
                [top_height, max(360, self.height() - top_height)]
            )
            return
        self._content_splitter.setOrientation(Qt.Orientation.Horizontal)
        nav_width = max(210, min(250, int(self.width() * 0.23)))
        self._content_splitter.setSizes(
            [nav_width, max(680, self.width() - nav_width)]
        )

    def _on_scene_edit_requested(self, entity_kind: str) -> None:
        target_key = {
            "geometry": "project.section.geometry",
            "source": "project.section.sources",
            "receiver": "project.section.receivers",
            "antenna": "project.section.libraries",
            "import": "project.section.libraries",
        }.get(entity_kind)
        if target_key is None:
            return
        for row, (title_key, _panel) in enumerate(self._sections):
            if title_key == target_key:
                self._section_nav.setCurrentRow(row)
                return
