from __future__ import annotations

from PySide6.QtCore import QSize, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
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
from ...domain.validation import ValidationIssue, ValidationResult, ValidationSeverity
from ...infrastructure.gprmax.command_registry import GprMaxCommandRegistry
from ..layouts.flow_layout import FlowLayout
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
        self._advanced_mode = False
        self._content_splitter_user_resized = False
        self._syncing_splitter_sizes = False
        self._persisted_content_splitter: dict[str, object] | None = None
        self._pending_section_key: str | None = None

        self._project_root_label = QLabel()
        self._project_root_label.setObjectName("SectionTitle")
        self._project_file_label = QLabel()
        self._project_file_label.setObjectName("SectionBody")
        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)
        self._validation_label = QLabel()
        self._validation_label.setObjectName("StatusBadge")
        self._validation_label.setProperty("statusTone", "neutral")
        self._validation_label.setWordWrap(True)
        self._workflow_hint = QLabel()
        self._workflow_hint.setObjectName("SectionBody")
        self._workflow_hint.setWordWrap(True)
        self._workflow_hint.setVisible(False)
        self._project_state_badge = QLabel()
        self._project_state_badge.setObjectName("StatusBadge")
        self._project_state_badge.setProperty("statusTone", "neutral")
        self._model_counts_label = QLabel()
        self._model_counts_label.setObjectName("ModelOverviewCounts")
        self._model_counts_label.setWordWrap(True)
        self._next_action_label = QLabel()
        self._next_action_label.setObjectName("ModelNextAction")
        self._next_action_label.setWordWrap(True)
        self._section_nav = QListWidget()
        self._section_nav.setObjectName("ContextNavigation")
        self._section_nav.setWordWrap(True)
        self._section_nav.currentRowChanged.connect(self._on_section_changed)
        self._section_stack = QStackedWidget()
        self._section_stack.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored,
        )
        self._section_buttons: dict[str, QPushButton] = {}
        self._validation_issue_buttons: list[QPushButton] = []

        self._save_button = QPushButton()
        self._save_button.setObjectName("PrimaryButton")
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
        self._all_sections: list[tuple[str, QWidget]] = [
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
        self._visible_sections: list[tuple[str, QWidget, int]] = []

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
        project_card.setObjectName("ModelOverviewCard")
        project_layout = QVBoxLayout(project_card)
        project_layout.setContentsMargins(20, 18, 20, 18)
        project_layout.setSpacing(8)

        self._project_heading_layout = QGridLayout()
        self._project_heading_layout.setContentsMargins(0, 0, 0, 0)
        self._project_heading_layout.setHorizontalSpacing(8)
        self._project_heading_layout.setVerticalSpacing(6)
        self._project_heading_layout.setColumnStretch(0, 1)
        self._project_heading_layout.addWidget(self._project_root_label, 0, 0)
        self._project_heading_layout.addWidget(self._project_state_badge, 0, 1)
        project_layout.addLayout(self._project_heading_layout)
        project_layout.addWidget(self._project_file_label)
        project_layout.addWidget(self._summary_label)
        overview_metrics = QHBoxLayout()
        overview_metrics.setContentsMargins(0, 0, 0, 0)
        overview_metrics.setSpacing(10)
        overview_metrics.addWidget(self._model_counts_label, 1)
        overview_metrics.addWidget(
            self._validation_label,
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        project_layout.addLayout(overview_metrics)
        project_layout.addWidget(self._next_action_label)
        project_layout.addWidget(self._workflow_hint)

        self._section_toolbar_card = QFrame()
        self._section_toolbar_card.setObjectName("ViewCard")
        self._section_toolbar_card.setVisible(False)
        section_toolbar_layout = QVBoxLayout(self._section_toolbar_card)
        section_toolbar_layout.setContentsMargins(14, 12, 14, 12)
        section_toolbar_layout.setSpacing(8)
        self._section_toolbar_title = QLabel()
        self._section_toolbar_title.setObjectName("SectionTitle")
        self._section_toolbar_hint = QLabel()
        self._section_toolbar_hint.setObjectName("SectionBody")
        self._section_toolbar_hint.setWordWrap(True)
        self._section_toolbar = QWidget()
        self._section_toolbar_layout = FlowLayout(
            self._section_toolbar,
            horizontal_spacing=8,
            vertical_spacing=8,
        )
        section_toolbar_layout.addWidget(self._section_toolbar_title)
        section_toolbar_layout.addWidget(self._section_toolbar_hint)
        section_toolbar_layout.addWidget(self._section_toolbar)

        self._validation_summary_card = QFrame()
        self._validation_summary_card.setObjectName("ValidationSummaryCard")
        validation_summary_layout = QVBoxLayout(self._validation_summary_card)
        validation_summary_layout.setContentsMargins(14, 12, 14, 12)
        validation_summary_layout.setSpacing(8)
        validation_summary_header = QHBoxLayout()
        self._validation_summary_title = QLabel()
        self._validation_summary_title.setObjectName("SectionTitle")
        self._validation_summary_badge = QLabel()
        self._validation_summary_badge.setObjectName("StatusBadge")
        self._validation_summary_badge.setProperty("statusTone", "neutral")
        validation_summary_header.addWidget(self._validation_summary_title, 1)
        validation_summary_header.addWidget(self._validation_summary_badge)
        self._validation_issue_container = QWidget()
        self._validation_issue_layout = QVBoxLayout(self._validation_issue_container)
        self._validation_issue_layout.setContentsMargins(0, 0, 0, 0)
        self._validation_issue_layout.setSpacing(6)
        validation_summary_layout.addLayout(validation_summary_header)
        validation_summary_layout.addWidget(self._validation_issue_container)

        nav_card = QFrame()
        nav_card.setObjectName("ViewCard")
        self._nav_card = nav_card
        nav_layout = QVBoxLayout(nav_card)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(10)
        self._nav_heading = QLabel()
        self._nav_heading.setObjectName("SectionTitle")
        nav_layout.addWidget(self._nav_heading)
        nav_layout.addWidget(self._section_nav, 1)
        self._nav_card.setVisible(True)

        for _, panel in self._all_sections:
            self._section_stack.addWidget(panel)

        self._content_splitter = configure_splitter(QSplitter())
        self._content_splitter.addWidget(nav_card)
        self._content_splitter.addWidget(self._section_stack)
        self._content_splitter.setStretchFactor(0, 0)
        self._content_splitter.setStretchFactor(1, 1)
        self._content_splitter.setSizes([230, 980])
        self._content_splitter.splitterMoved.connect(self._on_content_splitter_moved)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._header)
        layout.addWidget(self._subtitle)
        layout.addWidget(project_card)
        layout.addWidget(self._validation_summary_card)
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
            project.metadata.name if project else self._localization.text("project.no_project")
        )
        project_details = "\n".join(
            item
            for item in (
                str(project.root) if project else "",
                self._localization.text("project.manifest", path=project_file)
                if project_file
                else "",
            )
            if item
        )
        self._project_root_label.setToolTip(project_details)
        self._project_file_label.setText(
            self._localization.text("project.manifest", path=project_file or "-")
        )
        self._project_file_label.setVisible(False)
        self._summary_label.setVisible(project is None)

        if project is None:
            self._summary_label.setText(self._localization.text("project.summary.empty"))
            self._set_validation_label_text(
                self._localization.text("project.validation.empty"),
                "neutral",
            )
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
            self._set_validation_label(validation, is_dirty)
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
        self._refresh_project_workspace(validation, is_dirty)

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
            self._set_validation_label_text(
                self._localization.text("project.validation.empty"),
                "neutral",
            )
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
            self._set_validation_label(validation, True)
            self._workflow_hint.setText(self._localization.text("project.workflow_hint"))

        self._refresh_project_workspace(validation, True)
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

    def _set_validation_label(
        self,
        validation: ValidationResult | None,
        is_dirty: bool,
    ) -> None:
        tone = "success"
        if validation is None:
            tone = "neutral"
        elif validation.errors:
            tone = "error"
        elif validation.warnings or is_dirty:
            tone = "warning"
        self._set_validation_label_text(self._format_validation(validation, is_dirty), tone)

    def _set_validation_label_text(self, text: str, tone: str) -> None:
        self._set_status_badge(self._validation_label, text, tone)

    def _refresh_project_workspace(
        self,
        validation: ValidationResult | None,
        is_dirty: bool,
    ) -> None:
        self._refresh_model_overview(validation, is_dirty)
        self._refresh_validation_summary(validation)
        self._refresh_section_statuses(validation)

    def _refresh_model_overview(
        self,
        validation: ValidationResult | None,
        is_dirty: bool,
    ) -> None:
        project = self._current_project
        if project is None:
            self._set_status_badge(
                self._project_state_badge,
                self._localization.text("project.overview.state.no_project"),
                "neutral",
            )
            self._model_counts_label.setText(
                self._localization.text("project.overview.counts.empty")
            )
            self._next_action_label.setText(
                self._localization.text("project.next.no_project")
            )
            return

        state_key = "project.overview.state.modified" if is_dirty else "project.overview.state.saved"
        state_tone = "warning" if is_dirty else "success"
        self._set_status_badge(
            self._project_state_badge,
            self._localization.text(state_key),
            state_tone,
        )
        model = project.model
        libraries = len(model.geometry_imports) + len(model.antenna_models)
        advanced = len(project.advanced_input_overrides) + len(model.python_blocks)
        self._model_counts_label.setText(
            self._localization.text(
                "project.overview.counts",
                materials=len(model.materials),
                waveforms=len(model.waveforms),
                sources=len(model.sources),
                receivers=len(model.receivers),
                geometry=len(model.geometry),
                libraries=libraries,
                advanced=advanced,
            )
        )
        self._next_action_label.setText(
            self._localization.text(self._next_action_key(project, validation))
        )

    def _next_action_key(
        self,
        project: Project,
        validation: ValidationResult | None,
    ) -> str:
        if validation is not None and validation.errors:
            return "project.next.fix_errors"
        if not project.model.waveforms:
            return "project.next.add_waveform"
        if not project.model.sources:
            return "project.next.add_source"
        if not project.model.receivers:
            return "project.next.add_receiver"
        if not project.model.geometry and not project.model.geometry_imports and not project.model.antenna_models:
            return "project.next.add_geometry"
        if validation is not None and validation.warnings:
            return "project.next.review_warnings"
        return "project.next.ready"

    def _refresh_validation_summary(
        self,
        validation: ValidationResult | None,
    ) -> None:
        self._validation_summary_title.setText(
            self._localization.text("project.validation_summary.title")
        )
        self._clear_validation_issue_rows()

        if validation is None or not validation.issues:
            self._validation_summary_card.setVisible(False)
            return

        self._validation_summary_card.setVisible(True)
        tone = "error" if validation.errors else "warning"
        self._set_status_badge(
            self._validation_summary_badge,
            self._localization.text(
                "project.validation_summary.count_badge",
                errors=len(validation.errors),
                warnings=len(validation.warnings),
            ),
            tone,
        )
        for issue in validation.issues[:5]:
            self._add_validation_issue_row(issue)

    def _clear_validation_issue_rows(self) -> None:
        while self._validation_issue_layout.count():
            item = self._validation_issue_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._validation_issue_buttons = []

    def _add_validation_message_row(self, text: str) -> None:
        label = QLabel(text)
        label.setObjectName("ValidationIssueText")
        label.setWordWrap(True)
        self._validation_issue_layout.addWidget(label)

    def _add_validation_issue_row(self, issue: ValidationIssue) -> None:
        section_key = self._section_key_for_validation_path(issue.path)
        section_name = self._section_title(section_key)
        message = self._localization.translate_message(issue.message)
        severity = self._localization.severity_text(issue.severity.value)
        text = self._localization.text(
            "project.validation_summary.issue_row",
            severity=severity,
            section=section_name,
            message=self._short_text(message, 112),
        )
        button = QPushButton(text)
        button.setProperty("buttonRole", "validationIssue")
        button.setProperty("issueSeverity", issue.severity.value)
        button.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Fixed,
        )
        button.setToolTip(
            self._localization.text(
                "project.validation_summary.issue_tooltip",
                section=section_name,
                message=message,
            )
        )
        button.clicked.connect(lambda _checked=False, key=section_key: self._select_section_key(key))
        self._validation_issue_buttons.append(button)
        self._validation_issue_layout.addWidget(button)

    def _refresh_section_statuses(
        self,
        validation: ValidationResult | None,
    ) -> None:
        for row in range(self._section_nav.count()):
            item = self._section_nav.item(row)
            if item is None:
                continue
            section_key = item.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(section_key, str):
                continue
            status = self._section_status_for_key(section_key, validation)
            status_text = self._section_status_text(status)
            title = self._section_title(section_key)
            purpose = self._section_purpose(section_key)
            item.setText(title)
            item.setForeground(QColor(self._section_status_color(status)))
            item.setToolTip(
                self._localization.text(
                    "project.section_status.tooltip",
                    section=title,
                    status=status_text,
                    purpose=purpose,
                )
            )
            item.setData(Qt.ItemDataRole.UserRole + 2, status)

            button = self._section_buttons.get(section_key)
            if button is not None:
                button.setText(title)
                button.setProperty("sectionStatus", status)
                button.setToolTip(item.toolTip())
                self._repolish(button)

    def _section_status_for_key(
        self,
        section_key: str,
        validation: ValidationResult | None,
    ) -> str:
        if self._current_project is None:
            return "neutral"
        issues = self._validation_issues_for_section(section_key, validation)
        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            return "error"
        if issues:
            return "warning"
        if section_key == "project.section.advanced":
            return "advanced"
        if not self._section_has_content(section_key):
            return "empty"
        return "complete"

    def _validation_issues_for_section(
        self,
        section_key: str,
        validation: ValidationResult | None,
    ) -> list[ValidationIssue]:
        if validation is None:
            return []
        return [
            issue
            for issue in validation.issues
            if self._section_key_for_validation_path(issue.path) == section_key
        ]

    def _section_key_for_validation_path(self, path: str) -> str:
        if path.startswith(("metadata.", "model.title", "model.domain", "model.scan_trace_count")):
            return "project.section.area"
        if path.startswith("model.materials"):
            return "project.section.materials"
        if path.startswith("model.waveforms"):
            return "project.section.signal"
        if path.startswith("model.sources"):
            return "project.section.sources"
        if path.startswith("model.receivers"):
            return "project.section.receivers"
        if path.startswith(("model.geometry_imports", "model.antenna_models")):
            return "project.section.libraries"
        if path.startswith("model.geometry_views"):
            return "project.section.preview"
        if path.startswith("model.geometry"):
            return "project.section.geometry"
        if path.startswith(("advanced", "raw", "python", "model.python_blocks")):
            return "project.section.advanced"
        if path.startswith(("preview", "input", "run_config")):
            return "project.section.preview"
        return "project.section.area"

    def _section_has_content(self, section_key: str) -> bool:
        project = self._current_project
        if project is None:
            return False
        model = project.model
        if section_key == "project.section.scene":
            return any(
                (
                    model.geometry,
                    model.geometry_imports,
                    model.antenna_models,
                    model.sources,
                    model.receivers,
                )
            )
        if section_key == "project.section.area":
            return True
        if section_key == "project.section.materials":
            return bool(model.materials)
        if section_key == "project.section.signal":
            return bool(model.waveforms)
        if section_key == "project.section.sources":
            return bool(model.sources)
        if section_key == "project.section.receivers":
            return bool(model.receivers)
        if section_key == "project.section.geometry":
            return bool(model.geometry)
        if section_key == "project.section.libraries":
            return bool(model.geometry_imports or model.antenna_models)
        if section_key == "project.section.preview":
            return True
        if section_key == "project.section.advanced":
            return bool(project.advanced_input_overrides or model.python_blocks)
        return False

    def _section_title(self, section_key: str) -> str:
        return self._localization.text(section_key)

    def _section_purpose(self, section_key: str) -> str:
        section_id = section_key.removeprefix("project.section.")
        return self._localization.text(f"project.section_purpose.{section_id}")

    def _section_status_text(self, status: str) -> str:
        return self._localization.text(f"project.section_status.{status}")

    def _section_status_color(self, status: str) -> str:
        return {
            "complete": "#166534",
            "warning": "#92400e",
            "error": "#991b1b",
            "empty": "#94a3b8",
            "advanced": "#5b21b6",
        }.get(status, "#64748b")

    def _short_text(self, text: str, limit: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return f"{normalized[: max(0, limit - 1)].rstrip()}..."

    def _set_status_badge(self, label: QLabel, text: str, tone: str) -> None:
        label.setText(text)
        label.setProperty("statusTone", tone)
        self._repolish(label)

    def _repolish(self, widget: QWidget) -> None:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    def retranslate_ui(self) -> None:
        self._header.setText(self._localization.text("project.title"))
        self._subtitle.setText(self._localization.text("project.subtitle"))
        self._save_button.setText(self._localization.text("action.save_project"))
        self._nav_heading.setText(self._localization.text("project.navigation"))
        self._section_toolbar_title.setText(
            self._localization.text("project.toolbar.title")
        )
        self._section_toolbar_hint.setText(
            self._localization.text("project.toolbar.hint")
        )
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
        self._refresh_responsive_layout(force=True)

    def set_advanced_mode(self, enabled: bool) -> None:
        if self._advanced_mode == enabled:
            return
        self._advanced_mode = enabled
        self._retranslate_sections()

    def ui_state(self) -> dict[str, object]:
        state: dict[str, object] = {
            "content_splitter": self._splitter_state(self._content_splitter),
        }
        current_key = self._current_section_key()
        if current_key is not None:
            state["section_key"] = current_key
        scene_state = self._scene_panel.ui_state()
        if scene_state:
            state["scene"] = scene_state
        return state

    def apply_ui_state(self, state: dict[str, object] | None) -> None:
        if not isinstance(state, dict):
            return
        section_key = state.get("section_key")
        self._pending_section_key = section_key if isinstance(section_key, str) else None
        splitter_state = state.get("content_splitter")
        if isinstance(splitter_state, dict):
            self._persisted_content_splitter = splitter_state
        scene_state = state.get("scene")
        if isinstance(scene_state, dict):
            self._scene_panel.apply_ui_state(scene_state)
        self._retranslate_sections()
        self._refresh_responsive_layout(force=True)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_responsive_layout()

    def _retranslate_sections(self) -> None:
        current_key = self._current_section_key() or self._pending_section_key
        self._visible_sections = []
        with QSignalBlocker(self._section_nav):
            self._section_nav.clear()
            for stack_index, (title_key, panel) in enumerate(self._all_sections):
                if not self._advanced_mode and title_key == "project.section.advanced":
                    continue
                item = QListWidgetItem(self._localization.text(title_key))
                item.setSizeHint(QSize(180, 54))
                item.setData(Qt.ItemDataRole.UserRole, stack_index)
                item.setData(Qt.ItemDataRole.UserRole + 1, title_key)
                self._section_nav.addItem(item)
                self._visible_sections.append((title_key, panel, stack_index))

            target_row = self._row_for_section_key(current_key)
            if target_row < 0 and self._section_nav.count() > 0:
                target_row = 0
            if target_row >= 0:
                self._section_nav.setCurrentRow(target_row)

        self._rebuild_section_toolbar()
        self._refresh_section_statuses(self._validation_service.current_validation())
        if target_row >= 0:
            self._on_section_changed(target_row)

    def _on_section_changed(self, row: int) -> None:
        item = self._section_nav.item(row) if row >= 0 else None
        if item is None:
            return
        stack_index = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(stack_index, int):
            return
        self._pending_section_key = item.data(Qt.ItemDataRole.UserRole + 1)
        self._section_stack.setCurrentIndex(stack_index)
        self._sync_section_toolbar()

    def _rebuild_section_toolbar(self) -> None:
        while self._section_toolbar_layout.count():
            item = self._section_toolbar_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._section_buttons = {}
        for row in range(self._section_nav.count()):
            item = self._section_nav.item(row)
            if item is None:
                continue
            section_key = item.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(section_key, str):
                continue
            button = QPushButton(self._section_title(section_key))
            button.setCheckable(True)
            button.setProperty("sectionButton", True)
            button.setProperty("sectionStatus", "neutral")
            button.setToolTip(
                self._localization.text(
                    f"project.section_tip.{section_key.removeprefix('project.section.')}"
                )
            )
            button.clicked.connect(
                lambda _checked=False, key=section_key: self._select_section_key(key)
            )
            self._section_buttons[section_key] = button
            self._section_toolbar_layout.addWidget(button)
        self._sync_section_toolbar()

    def _select_section_key(self, section_key: str) -> None:
        row = self._row_for_section_key(section_key)
        if row >= 0:
            self._section_nav.setCurrentRow(row)

    def _sync_section_toolbar(self) -> None:
        current_key = self._current_section_key()
        for section_key, button in self._section_buttons.items():
            button.setChecked(section_key == current_key)

    def _refresh_responsive_layout(self, *, force: bool = False) -> None:
        self._refresh_project_heading_layout()
        orientation = Qt.Orientation.Horizontal
        orientation_changed = self._content_splitter.orientation() != orientation
        if orientation_changed:
            self._content_splitter.setOrientation(orientation)
            self._content_splitter_user_resized = False
        if force or orientation_changed or not self._content_splitter_user_resized:
            persisted_sizes = (
                self._splitter_sizes_for_orientation(orientation)
                if self.width() >= 980
                else None
            )
            if persisted_sizes is not None:
                self._apply_splitter_sizes(persisted_sizes)
                return
            if self.width() < 980:
                nav_width = max(148, min(190, int(self.width() * 0.21)))
            else:
                nav_width = max(210, min(250, int(self.width() * 0.23)))
            self._apply_splitter_sizes(
                [nav_width, max(320, self.width() - nav_width)]
            )

    def _refresh_project_heading_layout(self) -> None:
        self._project_heading_layout.removeWidget(self._save_button)
        if self.width() < 760:
            self._project_heading_layout.addWidget(
                self._save_button,
                1,
                0,
                1,
                2,
                Qt.AlignmentFlag.AlignLeft,
            )
            return
        self._project_heading_layout.addWidget(self._save_button, 0, 2)

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
        row = self._row_for_section_key(target_key)
        if row >= 0:
            self._section_nav.setCurrentRow(row)
            return

    def _apply_splitter_sizes(self, sizes: list[int]) -> None:
        self._syncing_splitter_sizes = True
        try:
            self._content_splitter.setSizes(sizes)
        finally:
            self._syncing_splitter_sizes = False

    def _on_content_splitter_moved(self, _pos: int, _index: int) -> None:
        if self._syncing_splitter_sizes:
            return
        self._content_splitter_user_resized = True

    def _current_section_key(self) -> str | None:
        item = self._section_nav.currentItem()
        value = item.data(Qt.ItemDataRole.UserRole + 1) if item is not None else None
        return value if isinstance(value, str) else None

    def _row_for_section_key(self, section_key: str | None) -> int:
        if not section_key:
            return -1
        for row in range(self._section_nav.count()):
            item = self._section_nav.item(row)
            if item is not None and item.data(Qt.ItemDataRole.UserRole + 1) == section_key:
                return row
        return -1

    def _splitter_state(self, splitter: QSplitter) -> dict[str, object]:
        orientation = (
            "horizontal"
            if splitter.orientation() == Qt.Orientation.Horizontal
            else "vertical"
        )
        return {
            "orientation": orientation,
            "sizes": [int(size) for size in splitter.sizes()],
        }

    def _splitter_sizes_for_orientation(
        self,
        orientation: Qt.Orientation,
    ) -> list[int] | None:
        state = self._persisted_content_splitter
        if not isinstance(state, dict):
            return None
        orientation_name = (
            "horizontal" if orientation == Qt.Orientation.Horizontal else "vertical"
        )
        if state.get("orientation") != orientation_name:
            return None
        sizes = state.get("sizes")
        if not isinstance(sizes, list) or len(sizes) != 2:
            return None
        if not all(isinstance(item, int) and item > 0 for item in sizes):
            return None
        return list(sizes)
