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
from ...domain.traces import BscanLoadResult
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
        embedded: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._results_service = results_service
        self._trace_service = trace_service
        self._bscan_service = bscan_service
        self._embedded = embedded
        self._project_root: Path | None = None
        self._run_summaries: dict[str, RunResultSummary] = {}
        self._metadata_cache: dict[str, ResultMetadata] = {}
        self._refresh_key: tuple[object, ...] | None = None
        self._loading = False
        self._card_headings: dict[str, QLabel] = {}
        self._preferred_ascan_output_by_run: dict[str, str] = {}
        self._preferred_bscan_output_by_run: dict[str, str] = {}
        self._preferred_ascan_receiver_by_run: dict[str, str] = {}
        self._preferred_bscan_receiver_by_run: dict[str, str] = {}
        self._preferred_ascan_components_by_run: dict[str, list[str]] = {}
        self._preferred_bscan_component_by_run: dict[str, str] = {}

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._run_list = QListWidget()
        self._run_list.currentRowChanged.connect(self._on_run_changed)
        self._artifact_list = QListWidget()

        self._refresh_button = QPushButton()
        self._refresh_button.clicked.connect(self.refresh_current_project)
        self._open_output_dir_button = QPushButton()
        self._open_output_dir_button.clicked.connect(self._open_output_directory)
        self._open_selected_file_button = QPushButton()
        self._open_selected_file_button.clicked.connect(self._open_selected_file)

        self._tabs = QTabWidget()
        self._tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tabs.addTab(self._build_ascan_panel(), "")
        self._tabs.addTab(self._build_bscan_panel(), "")

        toolbar = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        toolbar.addWidget(self._refresh_button)
        toolbar.addWidget(self._open_output_dir_button)
        toolbar.addWidget(self._open_selected_file_button)

        left_panel = self._build_card("results.card.runs", self._run_list)
        left_panel.setMinimumWidth(220)

        self._summary_panel = ResultSummaryPanel(localization)
        summary_card = self._build_card("results.card.summary", self._summary_panel)
        artifact_card = self._build_card("results.card.other_artifacts", self._artifact_list)

        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)
        details_layout.addWidget(summary_card)
        details_layout.addWidget(artifact_card, 1)

        self._bottom_splitter = QSplitter()
        self._bottom_splitter.addWidget(left_panel)
        self._bottom_splitter.addWidget(details_panel)
        self._bottom_splitter.setStretchFactor(0, 0)
        self._bottom_splitter.setStretchFactor(1, 1)
        self._bottom_splitter.setChildrenCollapsible(False)
        self._bottom_splitter.setSizes([320, 960])

        plot_card = self._build_card("results.card.plot", self._tabs)
        plot_card.setMinimumHeight(320 if embedded else 420)
        plot_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._page_splitter = QSplitter(Qt.Orientation.Vertical)
        self._page_splitter.addWidget(plot_card)
        self._page_splitter.addWidget(self._bottom_splitter)
        self._page_splitter.setStretchFactor(0, 4)
        self._page_splitter.setStretchFactor(1, 2)
        self._page_splitter.setChildrenCollapsible(False)
        self._page_splitter.setSizes([560 if embedded else 620, 280])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12 if embedded else 18)
        if not embedded:
            layout.addWidget(self._title)
            layout.addWidget(self._subtitle)
        layout.addLayout(toolbar)
        layout.addWidget(self._page_splitter, 1)

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
            self._sync_run_selection()
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

    def _build_ascan_panel(self) -> QWidget:
        self._ascan_output_combo = QComboBox()
        self._ascan_output_combo.currentIndexChanged.connect(self._on_ascan_output_changed)
        self._ascan_receiver_combo = QComboBox()
        self._ascan_receiver_combo.currentIndexChanged.connect(self._on_ascan_receiver_changed)
        self._ascan_component_list = QListWidget()
        self._ascan_component_list.setMinimumHeight(96)
        self._ascan_component_list.itemChanged.connect(self._on_ascan_component_item_changed)
        self._show_unmerged_checkbox = QCheckBox()
        self._show_unmerged_checkbox.setVisible(False)
        self._show_unmerged_checkbox.toggled.connect(self._on_ascan_output_filter_changed)
        self._ascan_status_label = QLabel()
        self._ascan_status_label.setWordWrap(True)

        self._ascan_output_label = QLabel()
        self._ascan_receiver_label = QLabel()
        self._ascan_components_label = QLabel()

        selectors = QWidget()
        selectors_layout = QFormLayout(selectors)
        selectors_layout.setContentsMargins(0, 0, 0, 0)
        selectors_layout.setSpacing(10)
        selectors_layout.addRow(self._ascan_output_label, self._ascan_output_combo)
        selectors_layout.addRow("", self._show_unmerged_checkbox)
        selectors_layout.addRow(self._ascan_receiver_label, self._ascan_receiver_combo)
        selectors_layout.addRow(self._ascan_components_label, self._ascan_component_list)

        self._trace_plot = TracePlotWidget(self._localization)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(selectors)
        layout.addWidget(self._trace_plot, 1)
        layout.addWidget(self._ascan_status_label)
        return panel

    def _build_bscan_panel(self) -> QWidget:
        self._bscan_output_combo = QComboBox()
        self._bscan_output_combo.currentIndexChanged.connect(self._on_bscan_output_changed)
        self._bscan_receiver_combo = QComboBox()
        self._bscan_receiver_combo.currentIndexChanged.connect(self._on_bscan_receiver_changed)
        self._bscan_component_combo = QComboBox()
        self._bscan_component_combo.currentIndexChanged.connect(self._on_bscan_component_changed)
        self._bscan_status_label = QLabel()
        self._bscan_status_label.setWordWrap(True)

        self._bscan_output_label = QLabel()
        self._bscan_receiver_label = QLabel()
        self._bscan_component_label = QLabel()

        selectors = QWidget()
        selectors_layout = QFormLayout(selectors)
        selectors_layout.setContentsMargins(0, 0, 0, 0)
        selectors_layout.setSpacing(10)
        selectors_layout.addRow(self._bscan_output_label, self._bscan_output_combo)
        selectors_layout.addRow(self._bscan_receiver_label, self._bscan_receiver_combo)
        selectors_layout.addRow(self._bscan_component_label, self._bscan_component_combo)

        self._bscan_view = BscanImageWidget(self._localization)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(selectors)
        layout.addWidget(self._bscan_view, 1)
        layout.addWidget(self._bscan_status_label)
        return panel

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
        self._artifact_list.clear()
        self._summary_panel.set_summary(summary, None)
        self._clear_ascan_panel(self._localization.text("results.status.select_trace"))
        self._clear_bscan_panel(self._localization.text("results.status.select_bscan_component"))

        if summary is None:
            self._loading = False
            return

        for artifact in summary.visualisation_artifacts:
            item = QListWidgetItem(artifact.name)
            item.setToolTip(str(artifact))
            item.setData(Qt.ItemDataRole.UserRole, str(artifact))
            self._artifact_list.addItem(item)

        summary_metadata = self._load_summary_metadata(summary)
        self._summary_panel.set_summary(summary, summary_metadata)
        self._loading = False

        self._populate_ascan_panel(summary)
        self._populate_bscan_panel(summary)

    def _populate_ascan_panel(self, summary: RunResultSummary) -> None:
        run_id = summary.run_record.run_id
        single_trace_files = [item for item in summary.output_files if not item.is_merged]
        toggle_available = self._can_show_unmerged_traces(summary)

        self._loading = True
        with QSignalBlocker(self._show_unmerged_checkbox):
            self._show_unmerged_checkbox.setVisible(toggle_available)
            self._show_unmerged_checkbox.setEnabled(toggle_available)
            if not toggle_available:
                self._show_unmerged_checkbox.setChecked(False)

        entries = self._ascan_output_entries(summary)
        with QSignalBlocker(self._ascan_output_combo):
            self._ascan_output_combo.clear()
            for label, path in entries:
                self._ascan_output_combo.addItem(label, str(path))
        self._loading = False

        if not entries:
            if toggle_available and single_trace_files:
                self._clear_ascan_panel(
                    self._localization.text("results.status.ascan_enable_unmerged"),
                    keep_toggle_state=True,
                )
            else:
                self._clear_ascan_panel(
                    self._localization.text("results.status.ascan_no_individual")
                )
            return

        preferred_path = self._preferred_ascan_output_by_run.get(run_id)
        target_index = self._find_combo_data(self._ascan_output_combo, preferred_path)
        if target_index < 0:
            target_index = 0
        with QSignalBlocker(self._ascan_output_combo):
            self._ascan_output_combo.setCurrentIndex(target_index)
        self._on_ascan_output_changed(target_index)

    def _populate_bscan_panel(self, summary: RunResultSummary) -> None:
        run_id = summary.run_record.run_id
        entries = self._bscan_output_entries(summary)

        self._loading = True
        with QSignalBlocker(self._bscan_output_combo):
            self._bscan_output_combo.clear()
            for label, path, mode in entries:
                self._bscan_output_combo.addItem(label, str(path))
                combo_index = self._bscan_output_combo.count() - 1
                self._bscan_output_combo.setItemData(
                    combo_index,
                    mode,
                    Qt.ItemDataRole.UserRole + 1,
                )
        self._loading = False

        if not entries:
            self._clear_bscan_panel(
                self._localization.translate_message(
                    "B-scan preview requires either a merged output file or at least two individual .out traces."
                )
            )
            return

        preferred_path = self._preferred_bscan_output_by_run.get(run_id)
        target_index = self._find_combo_data(self._bscan_output_combo, preferred_path)
        if target_index < 0:
            target_index = 0
        with QSignalBlocker(self._bscan_output_combo):
            self._bscan_output_combo.setCurrentIndex(target_index)
        self._on_bscan_output_changed(target_index)

    def _on_ascan_output_filter_changed(self, _checked: bool) -> None:
        if self._loading:
            return
        summary = self._current_summary()
        if summary is None:
            return
        self._populate_ascan_panel(summary)

    def _on_ascan_output_changed(self, index: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        output_path = self._combo_path(self._ascan_output_combo, index)
        if summary is None or output_path is None:
            self._clear_ascan_panel(self._localization.text("results.status.select_output"))
            return

        self._preferred_ascan_output_by_run[summary.run_record.run_id] = str(output_path)

        try:
            metadata = self._load_metadata(output_path)
        except ResultsReadError as exc:
            self._clear_ascan_panel(self._localization.translate_message(str(exc)))
            return

        self._loading = True
        with QSignalBlocker(self._ascan_receiver_combo):
            self._ascan_receiver_combo.clear()
            for receiver in metadata.receivers:
                self._ascan_receiver_combo.addItem(
                    self._localization.text(
                        "results.receiver_item",
                        receiver_id=receiver.receiver_id,
                        name=receiver.name,
                    ),
                    receiver.receiver_id,
                )
        self._loading = False

        if self._ascan_receiver_combo.count() == 0:
            self._clear_ascan_panel(self._localization.text("results.status.no_receivers"))
            return

        preferred_receiver = self._preferred_ascan_receiver_by_run.get(summary.run_record.run_id)
        target_index = self._find_combo_data(self._ascan_receiver_combo, preferred_receiver)
        if target_index < 0:
            target_index = 0
        with QSignalBlocker(self._ascan_receiver_combo):
            self._ascan_receiver_combo.setCurrentIndex(target_index)
        self._on_ascan_receiver_changed(target_index)

    def _on_ascan_receiver_changed(self, index: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        output_path = self._selected_ascan_output_path()
        receiver_id = self._ascan_receiver_combo.itemData(index) if index >= 0 else None
        receiver_id_text = receiver_id if isinstance(receiver_id, str) else None

        if summary is None or output_path is None or receiver_id_text is None:
            self._clear_ascan_panel(self._localization.text("results.status.select_trace"))
            return

        self._preferred_ascan_receiver_by_run[summary.run_record.run_id] = receiver_id_text
        components = self._trace_service.list_output_components(output_path, receiver_id_text)
        selected_components = [
            component
            for component in self._preferred_ascan_components_by_run.get(
                summary.run_record.run_id,
                [],
            )
            if component in components
        ] or (components[:1] if components else [])

        self._loading = True
        with QSignalBlocker(self._ascan_component_list):
            self._ascan_component_list.clear()
            for component in components:
                item = QListWidgetItem(component)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.CheckState.Checked
                    if component in selected_components
                    else Qt.CheckState.Unchecked
                )
                self._ascan_component_list.addItem(item)
        self._loading = False

        self._preferred_ascan_components_by_run[summary.run_record.run_id] = list(
            selected_components
        )
        self._render_ascan_for_selection()

    def _on_ascan_component_item_changed(self, _item: QListWidgetItem) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        if summary is not None:
            self._preferred_ascan_components_by_run[summary.run_record.run_id] = (
                self._selected_ascan_components()
            )
        self._render_ascan_for_selection()

    def _on_bscan_output_changed(self, index: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        output_path = self._combo_path(self._bscan_output_combo, index)
        if summary is None or output_path is None:
            self._clear_bscan_panel(
                self._localization.text("results.status.select_bscan_component")
            )
            return

        self._preferred_bscan_output_by_run[summary.run_record.run_id] = str(output_path)

        try:
            metadata = self._load_metadata(output_path)
        except ResultsReadError as exc:
            self._clear_bscan_panel(self._localization.translate_message(str(exc)))
            return

        self._loading = True
        with QSignalBlocker(self._bscan_receiver_combo):
            self._bscan_receiver_combo.clear()
            for receiver in metadata.receivers:
                self._bscan_receiver_combo.addItem(
                    self._localization.text(
                        "results.receiver_item",
                        receiver_id=receiver.receiver_id,
                        name=receiver.name,
                    ),
                    receiver.receiver_id,
                )
        self._loading = False

        if self._bscan_receiver_combo.count() == 0:
            self._clear_bscan_panel(self._localization.text("results.status.no_receivers"))
            return

        preferred_receiver = self._preferred_bscan_receiver_by_run.get(summary.run_record.run_id)
        target_index = self._find_combo_data(self._bscan_receiver_combo, preferred_receiver)
        if target_index < 0:
            target_index = 0
        with QSignalBlocker(self._bscan_receiver_combo):
            self._bscan_receiver_combo.setCurrentIndex(target_index)
        self._on_bscan_receiver_changed(target_index)

    def _on_bscan_receiver_changed(self, index: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        output_path = self._selected_bscan_output_path()
        receiver_id = self._bscan_receiver_combo.itemData(index) if index >= 0 else None
        receiver_id_text = receiver_id if isinstance(receiver_id, str) else None

        if summary is None or output_path is None or receiver_id_text is None:
            self._clear_bscan_panel(
                self._localization.text("results.status.select_bscan_component")
            )
            return

        self._preferred_bscan_receiver_by_run[summary.run_record.run_id] = receiver_id_text
        components = self._trace_service.list_output_components(output_path, receiver_id_text)

        self._loading = True
        with QSignalBlocker(self._bscan_component_combo):
            self._bscan_component_combo.clear()
            for component in components:
                self._bscan_component_combo.addItem(component, component)
        self._loading = False

        if self._bscan_component_combo.count() == 0:
            self._clear_bscan_panel(self._localization.text("results.status.no_components"))
            return

        preferred_component = self._preferred_bscan_component_by_run.get(
            summary.run_record.run_id
        )
        target_index = self._find_combo_data(self._bscan_component_combo, preferred_component)
        if target_index < 0:
            target_index = 0
        with QSignalBlocker(self._bscan_component_combo):
            self._bscan_component_combo.setCurrentIndex(target_index)
        self._on_bscan_component_changed(target_index)

    def _on_bscan_component_changed(self, index: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        receiver_id = self._bscan_receiver_combo.currentData()
        receiver_id_text = receiver_id if isinstance(receiver_id, str) else None
        component = self._bscan_component_combo.itemData(index) if index >= 0 else None
        component_text = component if isinstance(component, str) else None

        if summary is None or receiver_id_text is None or component_text is None:
            message = self._localization.text("results.status.select_bscan_component")
            self._bscan_view.set_result(_empty_bscan_result(message))
            self._bscan_status_label.setText(message)
            return

        self._preferred_bscan_component_by_run[summary.run_record.run_id] = component_text
        selected_summary = self._selected_bscan_summary(summary)
        bscan_result = self._bscan_service.load_bscan_if_available(
            selected_summary,
            receiver_id_text,
            component_text,
        )
        self._bscan_view.set_result(bscan_result)
        self._bscan_status_label.setText(
            self._localization.translate_message(bscan_result.message)
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
        if self._tabs.currentIndex() == 0:
            return self._selected_ascan_output_path()
        return self._selected_bscan_output_path()

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

    def _load_summary_metadata(self, summary: RunResultSummary) -> ResultMetadata | None:
        primary_output = summary.primary_output_file
        if primary_output is None:
            return None
        try:
            return self._load_metadata(primary_output.path)
        except ResultsReadError:
            return None

    def _render_ascan_for_selection(self) -> None:
        output_path = self._selected_ascan_output_path()
        receiver_id = self._ascan_receiver_combo.currentData()
        receiver_id_text = receiver_id if isinstance(receiver_id, str) else None
        selected_components = self._selected_ascan_components()

        if output_path is None or receiver_id_text is None:
            message = self._localization.text("results.status.select_trace")
            self._trace_plot.clear(message)
            self._ascan_status_label.setText(message)
            return

        if not selected_components:
            message = self._localization.text("results.status.select_ascan_component")
            self._trace_plot.clear(message)
            self._ascan_status_label.setText(message)
            return

        try:
            traces = self._trace_service.load_ascans(
                output_path,
                receiver_id_text,
                selected_components,
            )
        except ResultsReadError as exc:
            message = self._localization.translate_message(str(exc))
            self._trace_plot.clear(message)
            self._ascan_status_label.setText(message)
            return

        self._trace_plot.set_traces(traces)
        self._ascan_status_label.setText(
            self._localization.text(
                "results.ascan_multi_loaded",
                components=", ".join(trace.metadata.component for trace in traces),
                samples=len(traces[0].values) if traces else 0,
                dt=traces[0].metadata.dt_s if traces else 0.0,
            )
        )

    def _selected_ascan_components(self) -> list[str]:
        components: list[str] = []
        for row in range(self._ascan_component_list.count()):
            item = self._ascan_component_list.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                components.append(item.text())
        return components

    def _selected_ascan_output_path(self) -> Path | None:
        return self._combo_path(self._ascan_output_combo, self._ascan_output_combo.currentIndex())

    def _selected_bscan_output_path(self) -> Path | None:
        return self._combo_path(self._bscan_output_combo, self._bscan_output_combo.currentIndex())

    def _selected_bscan_output_mode(self) -> str | None:
        index = self._bscan_output_combo.currentIndex()
        if index < 0:
            return None
        value = self._bscan_output_combo.itemData(index, Qt.ItemDataRole.UserRole + 1)
        return value if isinstance(value, str) else None

    def _selected_bscan_summary(self, summary: RunResultSummary) -> RunResultSummary:
        mode = self._selected_bscan_output_mode()
        selected_path = self._selected_bscan_output_path()

        if mode == self._OUTPUT_MODE_STACKED:
            output_files = [item for item in summary.output_files if not item.is_merged]
        elif mode == self._OUTPUT_MODE_MERGED and selected_path is not None:
            output_files = [
                item
                for item in summary.output_files
                if item.is_merged and item.path == selected_path
            ]
        else:
            output_files = list(summary.output_files)

        if not output_files:
            output_files = list(summary.output_files)

        return RunResultSummary(
            run_record=summary.run_record,
            output_files=output_files,
            visualisation_artifacts=list(summary.visualisation_artifacts),
            issues=list(summary.issues),
        )

    def _ascan_output_entries(self, summary: RunResultSummary) -> list[tuple[str, Path]]:
        single_trace_files = [item for item in summary.output_files if not item.is_merged]
        has_merged = any(item.is_merged for item in summary.output_files)
        if has_merged and single_trace_files and not self._show_unmerged_checkbox.isChecked():
            return []
        return [(item.name, item.path) for item in single_trace_files]

    def _bscan_output_entries(self, summary: RunResultSummary) -> list[tuple[str, Path, str]]:
        merged_files = [item for item in summary.output_files if item.is_merged]
        if merged_files:
            return [
                (item.name, item.path, self._OUTPUT_MODE_MERGED)
                for item in merged_files
            ]

        single_trace_files = [item for item in summary.output_files if not item.is_merged]
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
        return []

    def _can_show_unmerged_traces(self, summary: RunResultSummary) -> bool:
        has_merged = any(item.is_merged for item in summary.output_files)
        single_trace_count = sum(1 for item in summary.output_files if not item.is_merged)
        return has_merged and single_trace_count > 0

    def _clear_results(self, message: str) -> None:
        self._run_list.clear()
        self._artifact_list.clear()
        self._summary_panel.set_summary(None, None)
        self._clear_ascan_panel(message)
        self._clear_bscan_panel(message)

    def _clear_ascan_panel(self, message: str, *, keep_toggle_state: bool = False) -> None:
        with QSignalBlocker(self._ascan_output_combo):
            self._ascan_output_combo.clear()
        with QSignalBlocker(self._ascan_receiver_combo):
            self._ascan_receiver_combo.clear()
        with QSignalBlocker(self._ascan_component_list):
            self._ascan_component_list.clear()
        if not keep_toggle_state:
            self._show_unmerged_checkbox.setVisible(False)
        self._trace_plot.clear(message)
        self._ascan_status_label.setText(message)

    def _clear_bscan_panel(self, message: str) -> None:
        with QSignalBlocker(self._bscan_output_combo):
            self._bscan_output_combo.clear()
        with QSignalBlocker(self._bscan_receiver_combo):
            self._bscan_receiver_combo.clear()
        with QSignalBlocker(self._bscan_component_combo):
            self._bscan_component_combo.clear()
        self._bscan_view.set_result(_empty_bscan_result(message))
        self._bscan_status_label.setText(message)

    def _combo_path(self, combo: QComboBox, index: int) -> Path | None:
        raw = combo.itemData(index) if index >= 0 else None
        return Path(raw) if isinstance(raw, str) else None

    def _find_combo_data(self, combo: QComboBox, value: str | None) -> int:
        if not value:
            return -1
        return combo.findData(value)

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
        self._tabs.setTabText(0, self._localization.text("results.tab.ascan"))
        self._tabs.setTabText(1, self._localization.text("results.tab.bscan"))
        self._ascan_output_label.setText(self._localization.text("results.ascan_output"))
        self._ascan_receiver_label.setText(self._localization.text("results.receiver"))
        self._ascan_components_label.setText(
            self._localization.text("results.ascan_components")
        )
        self._bscan_output_label.setText(self._localization.text("results.bscan_output"))
        self._bscan_receiver_label.setText(self._localization.text("results.receiver"))
        self._bscan_component_label.setText(
            self._localization.text("results.bscan_component")
        )
        self._show_unmerged_checkbox.setText(
            self._localization.text("results.show_unmerged")
        )
        self._summary_panel.retranslate_ui()
        self._trace_plot.retranslate_ui()
        self._bscan_view.retranslate_ui()
        for key, heading in self._card_headings.items():
            heading.setText(self._localization.text(key))

    def _refresh_responsive_layout(self) -> None:
        main_orientation = (
            Qt.Orientation.Horizontal if self.width() >= 1180 else Qt.Orientation.Vertical
        )
        self._bottom_splitter.setOrientation(main_orientation)
        if main_orientation == Qt.Orientation.Horizontal:
            self._bottom_splitter.setSizes([260, 900])
            return
        self._bottom_splitter.setSizes([260, 540])

    def _sync_run_selection(self) -> None:
        selected_run_id = self._results_service.viewer_state.selected_run_id
        if not selected_run_id:
            return

        for row in range(self._run_list.count()):
            item = self._run_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) != selected_run_id:
                continue
            if self._run_list.currentRow() == row:
                self._populate_run_details(self._run_summaries.get(selected_run_id))
                return
            with QSignalBlocker(self._run_list):
                self._run_list.setCurrentRow(row)
            self._on_run_changed(row)
            return


def _empty_bscan_result(message: str) -> BscanLoadResult:
    return BscanLoadResult(available=False, message=message, dataset=None)
