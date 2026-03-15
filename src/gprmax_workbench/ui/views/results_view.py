from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...application.services.bscan_service import BscanService
from ...application.services.results_service import ResultsService
from ...application.services.trace_service import TraceService
from ...domain.results import ResultMetadata, RunResultSummary
from ...infrastructure.results.hdf5_reader import ResultsReadError
from ..widgets.results.bscan_image_widget import BscanImageWidget
from ..widgets.results.summary_panel import ResultSummaryPanel
from ..widgets.results.trace_plot_widget import TracePlotWidget


class ResultsView(QWidget):
    def __init__(
        self,
        *,
        results_service: ResultsService,
        trace_service: TraceService,
        bscan_service: BscanService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._results_service = results_service
        self._trace_service = trace_service
        self._bscan_service = bscan_service
        self._project_root: Path | None = None
        self._run_summaries: dict[str, RunResultSummary] = {}
        self._metadata_cache: dict[str, ResultMetadata] = {}
        self._refresh_key: tuple[object, ...] | None = None
        self._loading = False

        title = QLabel("Results Viewer")
        title.setObjectName("ViewTitle")
        subtitle = QLabel(
            "Stage 5 focuses on run-centric result discovery, metadata, A-scan viewing, and a bounded B-scan preview workflow."
        )
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        self._status_label = QLabel("Open a project and select a completed run to inspect results.")
        self._status_label.setWordWrap(True)

        self._run_list = QListWidget()
        self._run_list.currentRowChanged.connect(self._on_run_changed)
        self._output_list = QListWidget()
        self._output_list.currentRowChanged.connect(self._on_output_changed)
        self._artifact_list = QListWidget()

        self._receiver_combo = QComboBox()
        self._receiver_combo.currentIndexChanged.connect(self._on_receiver_changed)
        self._component_combo = QComboBox()
        self._component_combo.currentIndexChanged.connect(self._on_component_changed)

        refresh_button = QPushButton("Refresh Results")
        refresh_button.clicked.connect(self.refresh_current_project)
        open_output_dir_button = QPushButton("Open Output Folder")
        open_output_dir_button.clicked.connect(self._open_output_directory)
        open_selected_file_button = QPushButton("Open Selected File")
        open_selected_file_button.clicked.connect(self._open_selected_file)

        toolbar = QHBoxLayout()
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(open_output_dir_button)
        toolbar.addWidget(open_selected_file_button)
        toolbar.addStretch(1)

        left_panel = self._build_card("Runs", self._run_list)
        left_panel.setMinimumWidth(300)

        self._summary_panel = ResultSummaryPanel()
        summary_card = self._build_card("Summary", self._summary_panel)

        output_card = self._build_card("Output files", self._output_list)
        artifact_card = self._build_card("Other artifacts", self._artifact_list)
        artifact_row = QHBoxLayout()
        artifact_row.addWidget(output_card, 1)
        artifact_row.addWidget(artifact_card, 1)

        selectors = QWidget()
        selectors_layout = QFormLayout(selectors)
        selectors_layout.setContentsMargins(0, 0, 0, 0)
        selectors_layout.addRow("Receiver", self._receiver_combo)
        selectors_layout.addRow("Component", self._component_combo)

        self._trace_plot = TracePlotWidget()
        self._bscan_view = BscanImageWidget()
        tabs = QTabWidget()
        tabs.addTab(self._trace_plot, "A-scan")
        tabs.addTab(self._bscan_view, "B-scan")

        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(summary_card)
        right_layout.addLayout(artifact_row)
        right_layout.addWidget(selectors)
        right_layout.addWidget(tabs, 1)
        right_layout.addWidget(self._status_label)

        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_content)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 1000])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(toolbar)
        layout.addWidget(splitter, 1)

        self._clear_results("Open a project and select a completed run to inspect results.")

    def refresh_project(self, project_root: Path | None) -> None:
        if project_root is None:
            self._project_root = None
            self._refresh_key = None
            self._loading = False
            self._clear_results("Open a project and select a completed run to inspect results.")
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
                f"{summary.run_record.run_id} | {summary.run_record.status.value}"
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
            self._clear_results("No run results were found for this project yet.")
            return

        self._run_list.setCurrentRow(target_row)

    def refresh_current_project(self) -> None:
        self.refresh_project(self._project_root)

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
        self._component_combo.clear()
        self._summary_panel.set_summary(summary, None)
        self._trace_plot.clear("Select an output file, receiver, and component.")
        self._bscan_view.set_result(
            _empty_bscan_result("Select an output file, receiver, and component.")
        )

        if summary is None:
            self._status_label.setText("Select a run to inspect results.")
            self._loading = False
            return

        for output_file in summary.output_files:
            item = QListWidgetItem(output_file.name)
            item.setToolTip(str(output_file.path))
            item.setData(Qt.ItemDataRole.UserRole, str(output_file.path))
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
            self._status_label.setText("\n".join(summary.issues) if summary.issues else "No output files are available for this run.")
            return

        self._output_list.setCurrentRow(target_row)

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
            self._status_label.setText("Select an output file to inspect it.")
            return

        try:
            metadata = self._load_metadata(output_path)
        except ResultsReadError as exc:
            self._summary_panel.set_summary(summary, None)
            self._receiver_combo.clear()
            self._component_combo.clear()
            self._trace_plot.clear(str(exc))
            self._bscan_view.set_result(_empty_bscan_result(str(exc)))
            self._status_label.setText(str(exc))
            return

        self._summary_panel.set_summary(summary, metadata)
        self._loading = True
        self._receiver_combo.clear()
        for receiver in metadata.receivers:
            self._receiver_combo.addItem(
                f"{receiver.receiver_id} | {receiver.name}",
                receiver.receiver_id,
            )
        selected_receiver_id = self._results_service.viewer_state.selected_receiver_id
        target_index = 0
        if selected_receiver_id:
            index = self._receiver_combo.findData(selected_receiver_id)
            target_index = index if index >= 0 else 0
        self._loading = False

        if self._receiver_combo.count() == 0:
            self._status_label.setText("No receivers were found in the selected output file.")
            self._trace_plot.clear("No receivers were found in the selected output file.")
            self._bscan_view.set_result(_empty_bscan_result("No receivers were found in the selected output file."))
            return

        self._receiver_combo.setCurrentIndex(target_index)

    def _on_receiver_changed(self, index: int) -> None:
        if self._loading:
            return

        output_path = self._results_service.selected_output_path()
        receiver_id = self._receiver_combo.itemData(index) if index >= 0 else None
        receiver_id_text = receiver_id if isinstance(receiver_id, str) else None
        self._results_service.select_receiver(receiver_id_text)

        if output_path is None or receiver_id_text is None:
            self._component_combo.clear()
            return

        components = self._trace_service.list_output_components(output_path, receiver_id_text)
        self._loading = True
        self._component_combo.clear()
        for component in components:
            self._component_combo.addItem(component, component)
        selected_component = self._results_service.viewer_state.selected_component
        target_index = 0
        if selected_component:
            index = self._component_combo.findData(selected_component)
            target_index = index if index >= 0 else 0
        self._loading = False

        if self._component_combo.count() == 0:
            self._trace_plot.clear("The selected receiver does not expose any output components.")
            self._bscan_view.set_result(_empty_bscan_result("The selected receiver does not expose any output components."))
            self._status_label.setText("The selected receiver does not expose any output components.")
            return

        self._component_combo.setCurrentIndex(target_index)

    def _on_component_changed(self, index: int) -> None:
        if self._loading:
            return

        summary = self._current_summary()
        output_path = self._results_service.selected_output_path()
        receiver_id = self._results_service.viewer_state.selected_receiver_id
        component = self._component_combo.itemData(index) if index >= 0 else None
        component_text = component if isinstance(component, str) else None
        self._results_service.select_component(component_text)

        if summary is None or output_path is None or receiver_id is None or component_text is None:
            self._trace_plot.clear("Select an output file, receiver, and component.")
            self._bscan_view.set_result(_empty_bscan_result("Select an output file, receiver, and component."))
            return

        status_messages: list[str] = []
        try:
            trace = self._trace_service.load_ascan(output_path, receiver_id, component_text)
        except ResultsReadError as exc:
            self._trace_plot.clear(str(exc))
            status_messages.append(str(exc))
        else:
            self._trace_plot.set_trace(trace)
            status_messages.append(
                f"A-scan loaded: {len(trace.values)} samples, dt={trace.metadata.dt_s:.6g} s."
            )

        bscan_result = self._bscan_service.load_bscan_if_available(
            summary,
            receiver_id,
            component_text,
        )
        self._bscan_view.set_result(bscan_result)
        status_messages.append(bscan_result.message)
        self._status_label.setText("\n".join(status_messages))

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

    def _clear_results(self, message: str) -> None:
        self._run_list.clear()
        self._output_list.clear()
        self._artifact_list.clear()
        self._receiver_combo.clear()
        self._component_combo.clear()
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

    def _build_card(self, title: str, content: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("ViewCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        heading = QLabel(title)
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        layout.addWidget(content)
        return card


def _empty_bscan_result(message: str):
    from ...domain.traces import BscanLoadResult

    return BscanLoadResult(available=False, message=message, dataset=None)
