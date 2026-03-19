from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...application.services.bscan_service import BscanService
from ...application.services.localization_service import LocalizationService
from ...application.services.results_service import ResultsService
from ...application.services.trace_service import TraceService
from ...domain.results import ResultMetadata, RunResultSummary
from ...infrastructure.results.hdf5_reader import ResultsReadError
from ..layouts.flow_layout import FlowLayout
from ..widgets.results.bscan_image_widget import BscanImageWidget
from ..widgets.results.summary_panel import ResultSummaryPanel
from ..widgets.results.trace_plot_widget import TracePlotWidget


class ResultsView(QWidget):
    _OUTPUT_MODE_FILE = "file"
    _OUTPUT_MODE_MERGED = "merged"
    _OUTPUT_MODE_STACKED = "stacked"

    def __init__(
        self,
        *,
        localization: LocalizationService,
        results_service: ResultsService,
        trace_service: TraceService,
        bscan_service: BscanService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._results_service = results_service
        self._trace_service = trace_service
        self._bscan_service = bscan_service
        self._project_root: Path | None = None
        self._run_summaries: dict[str, RunResultSummary] = {}
        self._metadata_cache: dict[str, ResultMetadata] = {}
        self._refresh_key: tuple[object, ...] | None = None
        self._loading = False
        self._card_headings: dict[str, QLabel] = {}

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)

        self._run_list = QListWidget()
        self._run_list.currentRowChanged.connect(self._on_run_changed)
        self._output_list = QListWidget()
        self._output_list.currentRowChanged.connect(self._on_output_changed)
        self._artifact_list = QListWidget()
        self._component_list = QListWidget()
        self._component_list.itemChanged.connect(self._on_ascan_component_item_changed)

        self._receiver_combo = QComboBox()
        self._receiver_combo.currentIndexChanged.connect(self._on_receiver_changed)
        self._bscan_component_combo = QComboBox()
        self._bscan_component_combo.currentIndexChanged.connect(self._on_bscan_component_changed)
        self._show_unmerged_checkbox = QCheckBox()
        self._show_unmerged_checkbox.setVisible(False)
        self._show_unmerged_checkbox.toggled.connect(self._on_output_filter_changed)

        self._refresh_button = QPushButton()
        self._refresh_button.clicked.connect(self.refresh_current_project)
        self._open_output_dir_button = QPushButton()
        self._open_output_dir_button.clicked.connect(self._open_output_directory)
        self._open_selected_file_button = QPushButton()
        self._open_selected_file_button.clicked.connect(self._open_selected_file)

        toolbar = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        toolbar.addWidget(self._refresh_button)
        toolbar.addWidget(self._open_output_dir_button)
        toolbar.addWidget(self._open_selected_file_button)

        left_panel = self._build_card("results.card.runs", self._run_list)
        left_panel.setMinimumWidth(240)

        self._summary_panel = ResultSummaryPanel(localization)
        summary_card = self._build_card("results.card.summary", self._summary_panel)

        output_panel = QWidget()
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(10)
        output_layout.addWidget(self._show_unmerged_checkbox)
        output_layout.addWidget(self._output_list, 1)
        output_card = self._build_card("results.card.output_files", output_panel)
        artifact_card = self._build_card("results.card.other_artifacts", self._artifact_list)
        self._artifact_splitter = QSplitter()
        self._artifact_splitter.addWidget(output_card)
        self._artifact_splitter.addWidget(artifact_card)
        self._artifact_splitter.setStretchFactor(0, 1)
        self._artifact_splitter.setStretchFactor(1, 1)
        self._artifact_splitter.setChildrenCollapsible(False)

        selectors = QWidget()
        selectors_layout = QFormLayout(selectors)
        selectors_layout.setContentsMargins(0, 0, 0, 0)
        self._receiver_label = QLabel()
        self._ascan_components_label = QLabel()
        self._bscan_component_label = QLabel()
        selectors_layout.addRow(self._receiver_label, self._receiver_combo)
        selectors_layout.addRow(self._ascan_components_label, self._component_list)
        selectors_layout.addRow(self._bscan_component_label, self._bscan_component_combo)

        self._trace_plot = TracePlotWidget(localization)
        self._bscan_view = BscanImageWidget(localization)
        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.addTab(self._trace_plot, "")
        tabs.addTab(self._bscan_view, "")
        self._tabs = tabs

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(10)
        plot_layout.addWidget(selectors)
        plot_layout.addWidget(tabs, 1)
        plot_layout.addWidget(self._status_label)

        plot_card = self._build_card("results.card.plot", plot_panel)
        plot_card.setMinimumHeight(420)
        plot_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)
        details_layout.addWidget(summary_card)
        details_layout.addWidget(self._artifact_splitter, 1)

        self._right_splitter = QSplitter(Qt.Orientation.Vertical)
        self._right_splitter.addWidget(plot_card)
        self._right_splitter.addWidget(details_panel)
        self._right_splitter.setStretchFactor(0, 3)
        self._right_splitter.setStretchFactor(1, 1)
        self._right_splitter.setChildrenCollapsible(False)
        self._right_splitter.setSizes([560, 260])

        self._main_splitter = QSplitter()
        self._main_splitter.addWidget(left_panel)
        self._main_splitter.addWidget(self._right_splitter)
        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)
        self._main_splitter.setSizes([280, 920])
        self._main_splitter.setChildrenCollapsible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addLayout(toolbar)
        layout.addWidget(self._main_splitter, 1)

        self.retranslate_ui()
        self._clear_results(self._localization.text("results.status.open_project"))
        self._refresh_responsive_layout()

    def refresh_project(self, project_root: Path | None) -> None:
        if project_root is None:
            self._project_root = None
            self._refresh_key = None
            self._loading = False
            self._clear_results(self._localization.text("results.status.open_project"))
            return

        summaries = self._results_service.refresh_results(project_root)
        refresh_key = self._build_refresh_key(project_root, summaries)
        if self._project_root == project_root and self._refresh_key == refresh_key:
            return

        self._project_root = project_root
        self._refresh_key = refresh_key
        self._metadata_cache.clear()
        self._loading = True
        self._run_list.clear()
        self._run_summaries = {
            summary.run_record.run_id: summary for summary in summaries
        }
        for summary in summaries:
            item = QListWidgetItem(
                self._localization.text(
                    "results.run_item",
                    run_id=summary.run_record.run_id,
                    status=self._localization.simulation_status_text(
                        summary.run_record.status.value
                    ),
                )
            )
            item.setToolTip(str(summary.run_record.output_directory))
            item.setData(Qt.ItemDataRole.UserRole, summary.run_record.run_id)
            self._run_list.addItem(item)

        selected_run_id = self._results_service.viewer_state.selected_run_id
        target_row = 0
        if selected_run_id:
            for row in range(self._run_list.count()):
                item = self._run_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == selected_run_id:
                    target_row = row
                    break

        self._loading = False
        if self._run_list.count() == 0:
            self._clear_results(self._localization.text("results.status.no_results"))
            return

        with QSignalBlocker(self._run_list):
            self._run_list.setCurrentRow(target_row)
        self._on_run_changed(target_row)

    def refresh_current_project(self) -> None:
        self.refresh_project(self._project_root)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_responsive_layout()

    def _on_output_filter_changed(self, _checked: bool) -> None:
        if self._loading:
            return
        self._populate_run_details(self._current_summary())

    def _on_run_changed(self, row: int) -> None:
        if self._loading:
            return

        item = self._run_list.item(row) if row >= 0 else None
        run_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        run_id_text = run_id if isinstance(run_id, str) else None
        self._results_service.select_run(run_id_text)
        summary = self._run_summaries.get(run_id_text or "")
        self._populate_run_details(summary)

    def _populate_run_details(self, summary: RunResultSummary | None) -> None:
        self._loading = True
        self._output_list.clear()
        self._artifact_list.clear()
        self._receiver_combo.clear()
        self._component_list.clear()
        self._bscan_component_combo.clear()
        self._summary_panel.set_summary(summary, None)
        self._trace_plot.clear(self._localization.text("results.status.select_trace"))
        self._bscan_view.set_result(
            _empty_bscan_result(self._localization.text("results.status.select_trace"))
        )

        if summary is None:
            self._status_label.setText(self._localization.text("results.status.select_run"))
            self._loading = False
            return

        output_entries = self._output_entries(summary)
        self._show_unmerged_checkbox.setVisible(self._can_toggle_unmerged(summary))
        self._show_unmerged_checkbox.setEnabled(self._can_toggle_unmerged(summary))

        for label, output_path, output_mode in output_entries:
            item = QListWidgetItem(label)
            item.setToolTip(str(output_path))
            item.setData(Qt.ItemDataRole.UserRole, str(output_path))
            item.setData(Qt.ItemDataRole.UserRole + 1, output_mode)
            self._output_list.addItem(item)

        for artifact in summary.visualisation_artifacts:
            item = QListWidgetItem(artifact.name)
            item.setToolTip(str(artifact))
            item.setData(Qt.ItemDataRole.UserRole, str(artifact))
            self._artifact_list.addItem(item)

        viewer_state = self._results_service.viewer_state
        target_output_path = viewer_state.selected_output_file
        target_row = 0
        if target_output_path:
            for row in range(self._output_list.count()):
                item = self._output_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == target_output_path:
                    target_row = row
                    break

        self._loading = False
        if self._output_list.count() == 0:
            self._status_label.setText(
                "\n".join(
                    self._localization.translate_message(issue)
                    for issue in summary.issues
                )
                if summary.issues
                else self._localization.text("results.status.no_output_files")
            )
            return

        with QSignalBlocker(self._output_list):
            self._output_list.setCurrentRow(target_row)
        self._on_output_changed(target_row)

    def _on_output_changed(self, row: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        item = self._output_list.item(row) if row >= 0 else None
        raw_path = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        output_path = Path(raw_path) if isinstance(raw_path, str) else None
        self._results_service.select_output_file(output_path)

        if summary is None or output_path is None:
            self._summary_panel.set_summary(summary, None)
            self._status_label.setText(self._localization.text("results.status.select_output"))
            return

        try:
            metadata = self._load_metadata(output_path)
        except ResultsReadError as exc:
            self._summary_panel.set_summary(summary, None)
            self._receiver_combo.clear()
            self._component_list.clear()
            self._bscan_component_combo.clear()
            message = self._localization.translate_message(str(exc))
            self._trace_plot.clear(message)
            self._bscan_view.set_result(_empty_bscan_result(message))
            self._status_label.setText(message)
            return

        self._summary_panel.set_summary(summary, metadata)
        self._loading = True
        with QSignalBlocker(self._receiver_combo):
            self._receiver_combo.clear()
            for receiver in metadata.receivers:
                self._receiver_combo.addItem(
                    self._localization.text(
                        "results.receiver_item",
                        receiver_id=receiver.receiver_id,
                        name=receiver.name,
                    ),
                    receiver.receiver_id,
                )
        selected_receiver_id = self._results_service.viewer_state.selected_receiver_id
        target_index = 0
        if selected_receiver_id:
            index = self._receiver_combo.findData(selected_receiver_id)
            target_index = index if index >= 0 else 0
        self._loading = False

        if self._receiver_combo.count() == 0:
            message = self._localization.text("results.status.no_receivers")
            self._status_label.setText(message)
            self._trace_plot.clear(message)
            self._bscan_view.set_result(_empty_bscan_result(message))
            return

        output_mode = self._selected_output_mode()
        if output_mode in {self._OUTPUT_MODE_MERGED, self._OUTPUT_MODE_STACKED}:
            self._tabs.setCurrentIndex(1)
        else:
            self._tabs.setCurrentIndex(0)

        with QSignalBlocker(self._receiver_combo):
            self._receiver_combo.setCurrentIndex(target_index)
        self._on_receiver_changed(target_index)

    def _on_receiver_changed(self, index: int) -> None:
        if self._loading:
            return

        output_path = self._results_service.selected_output_path()
        receiver_id = self._receiver_combo.itemData(index) if index >= 0 else None
        receiver_id_text = receiver_id if isinstance(receiver_id, str) else None
        self._results_service.select_receiver(receiver_id_text)

        if output_path is None or receiver_id_text is None:
            self._component_list.clear()
            self._bscan_component_combo.clear()
            return

        components = self._trace_service.list_output_components(output_path, receiver_id_text)
        self._loading = True
        saved_ascan_components = self._results_service.viewer_state.selected_ascan_components
        selected_ascan_components = [
            component for component in saved_ascan_components if component in components
        ] or (components[:1] if components else [])
        with QSignalBlocker(self._component_list):
            self._component_list.clear()
            for component in components:
                item = QListWidgetItem(component)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.CheckState.Checked
                    if component in selected_ascan_components
                    else Qt.CheckState.Unchecked
                )
                self._component_list.addItem(item)

        selected_component = self._results_service.viewer_state.selected_component
        target_index = 0
        if selected_component:
            index = self._bscan_component_combo.findData(selected_component)
            target_index = index if index >= 0 else 0
        with QSignalBlocker(self._bscan_component_combo):
            self._bscan_component_combo.clear()
            for component in components:
                self._bscan_component_combo.addItem(component, component)
            if components:
                restored_index = self._bscan_component_combo.findData(selected_component)
                target_index = restored_index if restored_index >= 0 else 0
        self._loading = False

        if self._bscan_component_combo.count() == 0:
            message = self._localization.text("results.status.no_components")
            self._trace_plot.clear(message)
            self._bscan_view.set_result(_empty_bscan_result(message))
            self._status_label.setText(message)
            return

        self._results_service.select_ascan_components(selected_ascan_components)
        self._render_ascan_for_selection()
        with QSignalBlocker(self._bscan_component_combo):
            self._bscan_component_combo.setCurrentIndex(target_index)
        self._on_bscan_component_changed(target_index)

    def _on_ascan_component_item_changed(self, _item: QListWidgetItem) -> None:
        if self._loading:
            return
        selected_components = self._selected_ascan_components()
        self._results_service.select_ascan_components(selected_components)
        self._render_ascan_for_selection()

    def _on_bscan_component_changed(self, index: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        output_path = self._results_service.selected_output_path()
        receiver_id = self._results_service.viewer_state.selected_receiver_id
        component = self._bscan_component_combo.itemData(index) if index >= 0 else None
        component_text = component if isinstance(component, str) else None
        self._results_service.select_component(component_text)

        if summary is None or output_path is None or receiver_id is None or component_text is None:
            message = self._localization.text("results.status.select_bscan_component")
            self._bscan_view.set_result(_empty_bscan_result(message))
            self._append_status_message(message)
            return

        bscan_result = self._bscan_service.load_bscan_if_available(
            summary,
            receiver_id,
            component_text,
        )
        self._bscan_view.set_result(bscan_result)
        self._append_status_message(
            self._localization.translate_message(bscan_result.message),
            replace=False,
        )

    def _open_output_directory(self) -> None:
        summary = self._current_summary()
        path = self._results_service.open_output_directory(summary)
        if path is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_selected_file(self) -> None:
        selected = self._selected_artifact_or_output()
        if selected is None:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(selected)))

    def _selected_artifact_or_output(self) -> Path | None:
        artifact_item = self._artifact_list.currentItem()
        if artifact_item is not None:
            value = artifact_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(value, str):
                return Path(value)
        output_item = self._output_list.currentItem()
        if output_item is None:
            return None
        value = output_item.data(Qt.ItemDataRole.UserRole)
        return Path(value) if isinstance(value, str) else None

    def _current_summary(self) -> RunResultSummary | None:
        run_id = self._results_service.viewer_state.selected_run_id
        if not run_id:
            return None
        return self._run_summaries.get(run_id)

    def _load_metadata(self, output_path: Path) -> ResultMetadata:
        key = str(output_path.resolve())
        cached = self._metadata_cache.get(key)
        if cached is not None:
            return cached
        metadata = self._trace_service.load_result_metadata(output_path)
        self._metadata_cache[key] = metadata
        return metadata

    def _render_ascan_for_selection(self) -> None:
        output_path = self._results_service.selected_output_path()
        receiver_id = self._results_service.viewer_state.selected_receiver_id
        selected_components = self._selected_ascan_components()
        if output_path is None or receiver_id is None:
            message = self._localization.text("results.status.select_trace")
            self._trace_plot.clear(message)
            self._append_status_message(message)
            return

        output_mode = self._selected_output_mode()
        if output_mode in {self._OUTPUT_MODE_MERGED, self._OUTPUT_MODE_STACKED}:
            message = self._localization.text("results.status.ascan_merged_only")
            self._trace_plot.clear(message)
            self._append_status_message(message)
            return

        if not selected_components:
            message = self._localization.text("results.status.select_ascan_component")
            self._trace_plot.clear(message)
            self._append_status_message(message)
            return

        try:
            traces = self._trace_service.load_ascans(
                output_path,
                receiver_id,
                selected_components,
            )
        except ResultsReadError as exc:
            message = self._localization.translate_message(str(exc))
            self._trace_plot.clear(message)
            self._append_status_message(message)
            return

        self._trace_plot.set_traces(traces)
        self._append_status_message(
            self._localization.text(
                "results.ascan_multi_loaded",
                components=", ".join(trace.metadata.component for trace in traces),
                samples=len(traces[0].values) if traces else 0,
                dt=traces[0].metadata.dt_s if traces else 0.0,
            )
        )

    def _selected_ascan_components(self) -> list[str]:
        components: list[str] = []
        for row in range(self._component_list.count()):
            item = self._component_list.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                components.append(item.text())
        return components

    def _output_entries(self, summary: RunResultSummary) -> list[tuple[str, Path, str]]:
        merged_files = [item for item in summary.output_files if item.is_merged]
        single_trace_files = [item for item in summary.output_files if not item.is_merged]
        if not self._show_unmerged_checkbox.isChecked():
            if merged_files:
                return [
                    (item.name, item.path, self._OUTPUT_MODE_MERGED)
                    for item in merged_files
                ]
            if len(single_trace_files) >= 2:
                primary = single_trace_files[0]
                return [
                    (
                        self._localization.text(
                            "results.output.stacked_bscan",
                            count=len(single_trace_files),
                        ),
                        primary.path,
                        self._OUTPUT_MODE_STACKED,
                    )
                ]
        return [
            (
                item.name,
                item.path,
                self._OUTPUT_MODE_MERGED if item.is_merged else self._OUTPUT_MODE_FILE,
            )
            for item in summary.output_files
        ]

    def _can_toggle_unmerged(self, summary: RunResultSummary) -> bool:
        has_merged = any(item.is_merged for item in summary.output_files)
        single_trace_count = sum(1 for item in summary.output_files if not item.is_merged)
        return (has_merged and single_trace_count > 0) or single_trace_count >= 2

    def _selected_output_mode(self) -> str | None:
        item = self._output_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole + 1)
        return value if isinstance(value, str) else None

    def _append_status_message(self, message: str, *, replace: bool = True) -> None:
        if replace or not self._status_label.text().strip():
            self._status_label.setText(message)
            return
        parts = [part for part in self._status_label.text().splitlines() if part.strip()]
        if message not in parts:
            parts.append(message)
        self._status_label.setText("\n".join(parts))

    def _clear_results(self, message: str) -> None:
        self._run_list.clear()
        self._output_list.clear()
        self._artifact_list.clear()
        self._receiver_combo.clear()
        self._component_list.clear()
        self._bscan_component_combo.clear()
        self._show_unmerged_checkbox.setVisible(False)
        self._summary_panel.set_summary(None, None)
        self._trace_plot.clear(message)
        self._bscan_view.set_result(_empty_bscan_result(message))
        self._status_label.setText(message)

    def _build_refresh_key(
        self,
        project_root: Path,
        summaries: list[RunResultSummary],
    ) -> tuple[object, ...]:
        items: list[object] = [str(project_root)]
        for summary in summaries:
            items.extend(
                (
                    summary.run_record.run_id,
                    summary.run_record.status.value,
                    summary.run_record.exit_code,
                    tuple(item.name for item in summary.output_files),
                    tuple(path.name for path in summary.visualisation_artifacts),
                )
            )
        return tuple(items)

    def _build_card(self, title_key: str, content: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("ViewCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        heading = QLabel()
        heading.setObjectName("SectionTitle")
        self._card_headings[title_key] = heading
        layout.addWidget(heading)
        layout.addWidget(content)
        return card

    def retranslate_ui(self) -> None:
        self._title.setText(self._localization.text("results.title"))
        self._subtitle.setText(self._localization.text("results.subtitle"))
        self._refresh_button.setText(self._localization.text("results.action.refresh"))
        self._open_output_dir_button.setText(
            self._localization.text("results.action.open_output")
        )
        self._open_selected_file_button.setText(
            self._localization.text("results.action.open_selected")
        )
        self._receiver_label.setText(self._localization.text("results.receiver"))
        self._ascan_components_label.setText(
            self._localization.text("results.ascan_components")
        )
        self._bscan_component_label.setText(
            self._localization.text("results.bscan_component")
        )
        self._show_unmerged_checkbox.setText(
            self._localization.text("results.show_unmerged")
        )
        self._tabs.setTabText(0, self._localization.text("results.tab.ascan"))
        self._tabs.setTabText(1, self._localization.text("results.tab.bscan"))
        self._summary_panel.retranslate_ui()
        self._trace_plot.retranslate_ui()
        self._bscan_view.retranslate_ui()
        for key, heading in self._card_headings.items():
            heading.setText(self._localization.text(key))

    def _refresh_responsive_layout(self) -> None:
        main_orientation = (
            Qt.Orientation.Horizontal if self.width() >= 1180 else Qt.Orientation.Vertical
        )
        artifact_orientation = (
            Qt.Orientation.Horizontal if self.width() >= 1320 else Qt.Orientation.Vertical
        )
        self._main_splitter.setOrientation(main_orientation)
        self._artifact_splitter.setOrientation(artifact_orientation)


def _empty_bscan_result(message: str):
    from ...domain.traces import BscanLoadResult

    return BscanLoadResult(available=False, message=message, dataset=None)
