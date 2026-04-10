from __future__ import annotations

import shlex
from contextlib import ExitStack

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ...application.services.localization_service import LocalizationService
from ...domain.execution_status import SimulationMode
from ...domain.gprmax_config import SimulationRunConfig
from ...domain.simulation import SimulationRunRecord
from ..layouts.flow_layout import FlowLayout
from ..splitters import configure_splitter
from ..widgets.metric_tile import MetricTile


class SimulationConfigurationError(ValueError):
    """Raised when simulation settings cannot be parsed from the UI form."""


class SimulationView(QWidget):
    preview_requested = Signal()
    export_requested = Signal()
    start_requested = Signal()
    retry_requested = Signal()
    cancel_requested = Signal()
    open_run_directory_requested = Signal()
    open_output_directory_requested = Signal()
    configuration_changed = Signal()

    def __init__(
        self,
        *,
        localization: LocalizationService,
        runtime_label: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._card_headings: dict[str, QLabel] = {}
        self._start_allowed = False
        self._run_in_progress = False
        self._has_retry_target = False
        self._has_project = False
        self._advanced_mode = False
        self._top_splitter_user_resized = False
        self._content_splitter_user_resized = False
        self._syncing_splitter_sizes = False
        self._persisted_top_splitter: dict[str, object] | None = None
        self._persisted_content_splitter: dict[str, object] | None = None
        self._pending_section_key: str | None = None
        self._run_state_signature: tuple[object, ...] | None = None

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")

        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._runtime_label = QLabel(runtime_label)
        self._readiness_state_label = QLabel()
        self._readiness_state_label.setWordWrap(True)
        self._project_state_label = QLabel()
        self._project_state_label.setWordWrap(True)
        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._validation_label = QLabel()
        self._validation_label.setWordWrap(True)
        self._section_nav = QListWidget()
        self._section_nav.setObjectName("ContextNavigation")
        self._section_nav.currentRowChanged.connect(self._on_section_changed)
        self._section_stack = QStackedWidget()
        self._section_stack.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )

        self._readiness_tile = MetricTile()
        self._mode_tile = MetricTile()
        self._runs_tile = MetricTile()
        self._activity_tile = MetricTile()

        self._mode_combo = QComboBox()
        self._mode_combo.addItem("", SimulationMode.NORMAL.value)
        self._mode_combo.addItem("", SimulationMode.GEOMETRY_ONLY.value)
        self._mode_combo.currentIndexChanged.connect(self._on_configuration_widget_changed)

        self._num_runs_spinbox = QSpinBox()
        self._num_runs_spinbox.setRange(1, 1_000_000)
        self._num_runs_spinbox.setValue(1)
        self._num_runs_spinbox.valueChanged.connect(self._on_configuration_widget_changed)

        self._restart_spinbox = QSpinBox()
        self._restart_spinbox.setRange(0, 1_000_000)
        self._restart_spinbox.setValue(0)

        self._mpi_tasks_spinbox = QSpinBox()
        self._mpi_tasks_spinbox.setRange(0, 4096)
        self._mpi_tasks_spinbox.setValue(0)

        self._geometry_fixed_checkbox = QCheckBox()
        self._write_processed_checkbox = QCheckBox()
        self._benchmark_checkbox = QCheckBox()
        self._mpi_no_spawn_checkbox = QCheckBox()
        self._extra_args_edit = QLineEdit()
        self._extra_args_edit.setPlaceholderText("")
        self._restart_spinbox.valueChanged.connect(self._on_configuration_widget_changed)
        self._mpi_tasks_spinbox.valueChanged.connect(self._on_configuration_widget_changed)
        self._geometry_fixed_checkbox.toggled.connect(self._on_configuration_widget_changed)
        self._write_processed_checkbox.toggled.connect(self._on_configuration_widget_changed)
        self._benchmark_checkbox.toggled.connect(self._on_configuration_widget_changed)
        self._mpi_no_spawn_checkbox.toggled.connect(self._on_configuration_widget_changed)
        self._extra_args_edit.textChanged.connect(self._on_configuration_widget_changed)

        self._preview_text = QPlainTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setPlaceholderText("")

        self._log_text = QPlainTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setPlaceholderText("")

        self._run_history = QListWidget()
        self._run_history.currentRowChanged.connect(lambda _row: self._update_action_state())

        self._preview_button = QPushButton()
        self._preview_button.clicked.connect(self.preview_requested.emit)

        self._export_button = QPushButton()
        self._export_button.clicked.connect(self.export_requested.emit)

        self._start_button = QPushButton()
        self._start_button.setObjectName("PrimaryButton")
        self._start_button.clicked.connect(self.start_requested.emit)

        self._retry_button = QPushButton()
        self._retry_button.clicked.connect(self.retry_requested.emit)

        self._cancel_button = QPushButton()
        self._cancel_button.clicked.connect(self.cancel_requested.emit)

        self._open_run_button = QPushButton()
        self._open_run_button.clicked.connect(self.open_run_directory_requested.emit)

        self._open_output_button = QPushButton()
        self._open_output_button.clicked.connect(self.open_output_directory_requested.emit)

        self._action_bar = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        self._action_bar.addWidget(self._start_button)
        self._action_bar.addWidget(self._retry_button)
        self._action_bar.addWidget(self._preview_button)
        self._action_bar.addWidget(self._export_button)
        self._action_bar.addWidget(self._cancel_button)
        self._action_bar.addWidget(self._open_run_button)
        self._action_bar.addWidget(self._open_output_button)

        metrics_row = FlowLayout(horizontal_spacing=12, vertical_spacing=12)
        metrics_row.addWidget(self._readiness_tile)
        metrics_row.addWidget(self._mode_tile)
        metrics_row.addWidget(self._runs_tile)
        metrics_row.addWidget(self._activity_tile)

        status_card = self._build_card(
            "simulation.status_card",
            self._build_runtime_widget(),
        )
        status_card.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        config_card = self._build_card(
            "simulation.config_card",
            self._build_config_widget(),
        )
        config_card.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        history_card = self._build_card("simulation.history_card", self._run_history)
        history_card.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )

        self._top_splitter = configure_splitter(QSplitter())
        self._top_splitter.addWidget(status_card)
        self._top_splitter.addWidget(config_card)
        self._top_splitter.setStretchFactor(0, 1)
        self._top_splitter.setStretchFactor(1, 1)
        self._top_splitter.splitterMoved.connect(self._on_top_splitter_moved)

        launch_page = QWidget()
        launch_layout = QVBoxLayout(launch_page)
        launch_layout.setContentsMargins(0, 0, 0, 0)
        launch_layout.setSpacing(16)
        launch_layout.addLayout(metrics_row)
        launch_layout.addWidget(self._top_splitter)
        launch_page.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        self._launch_page = launch_page

        preview_page = QWidget()
        preview_layout = QVBoxLayout(preview_page)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(16)
        preview_layout.addWidget(
            self._build_card("simulation.preview_card", self._preview_text),
            1,
        )
        preview_page.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        self._preview_page = preview_page

        logs_page = QWidget()
        logs_layout = QVBoxLayout(logs_page)
        logs_layout.setContentsMargins(0, 0, 0, 0)
        logs_layout.setSpacing(16)
        logs_layout.addWidget(
            self._build_card("simulation.log_card", self._log_text),
            1,
        )
        logs_layout.addWidget(history_card, 1)
        logs_page.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        self._log_page = logs_page

        self._sections = [
            "simulation.section.launch",
            "simulation.section.preview",
            "simulation.section.logs",
        ]
        self._section_stack.addWidget(self._launch_page)
        self._section_stack.addWidget(self._preview_page)
        self._section_stack.addWidget(self._log_page)

        nav_card = QFrame()
        nav_card.setObjectName("ViewCard")
        nav_layout = QVBoxLayout(nav_card)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(10)
        self._nav_heading = QLabel()
        self._nav_heading.setObjectName("SectionTitle")
        nav_layout.addWidget(self._nav_heading)
        nav_layout.addWidget(self._section_nav, 1)

        self._content_splitter = configure_splitter(QSplitter())
        self._content_splitter.addWidget(nav_card)
        self._content_splitter.addWidget(self._section_stack)
        self._content_splitter.setStretchFactor(0, 0)
        self._content_splitter.setStretchFactor(1, 1)
        self._content_splitter.setSizes([240, 980])
        self._content_splitter.splitterMoved.connect(self._on_content_splitter_moved)

        self._workspace_container = QWidget()
        workspace_layout = QVBoxLayout(self._workspace_container)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(16)
        workspace_layout.addLayout(self._action_bar)
        workspace_layout.addWidget(self._content_splitter, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._workspace_container, 1)

        self.retranslate_ui()
        self._section_nav.setCurrentRow(0)
        self.set_readiness_state(
            summary=self._localization.text("simulation.readiness.no_project"),
            caption=runtime_label,
            start_allowed=False,
        )
        self.set_run_state(None, [])
        self.set_project_state(project_name=None, is_dirty=False)
        self._refresh_configuration_summary()
        self._refresh_responsive_layout(force=True)

    def current_configuration(self) -> SimulationRunConfig:
        mode = SimulationMode(self._mode_combo.currentData())
        restart_from = self._restart_spinbox.value() or None
        mpi_tasks = self._mpi_tasks_spinbox.value() or None
        try:
            extra_arguments = (
                shlex.split(self._extra_args_edit.text(), posix=False)
                if self._extra_args_edit.text().strip()
                else []
            )
        except ValueError as exc:
            raise SimulationConfigurationError(
                self._localization.text("simulation.invalid_extra_args")
            ) from exc

        return SimulationRunConfig(
            mode=mode,
            use_gpu=False,
            gpu_device_ids=[],
            benchmark=self._benchmark_checkbox.isChecked(),
            geometry_fixed=self._geometry_fixed_checkbox.isChecked(),
            write_processed=self._write_processed_checkbox.isChecked(),
            num_model_runs=self._num_runs_spinbox.value(),
            restart_from_model=restart_from,
            mpi_tasks=mpi_tasks,
            mpi_no_spawn=self._mpi_no_spawn_checkbox.isChecked(),
            extra_arguments=extra_arguments,
        )

    def set_configuration(self, configuration: SimulationRunConfig) -> None:
        with ExitStack() as stack:
            stack.enter_context(QSignalBlocker(self._mode_combo))
            stack.enter_context(QSignalBlocker(self._num_runs_spinbox))
            stack.enter_context(QSignalBlocker(self._restart_spinbox))
            stack.enter_context(QSignalBlocker(self._mpi_tasks_spinbox))
            stack.enter_context(QSignalBlocker(self._geometry_fixed_checkbox))
            stack.enter_context(QSignalBlocker(self._write_processed_checkbox))
            stack.enter_context(QSignalBlocker(self._benchmark_checkbox))
            stack.enter_context(QSignalBlocker(self._mpi_no_spawn_checkbox))
            stack.enter_context(QSignalBlocker(self._extra_args_edit))

            mode_index = self._mode_combo.findData(configuration.mode.value)
            self._mode_combo.setCurrentIndex(max(mode_index, 0))
            self._num_runs_spinbox.setValue(max(configuration.num_model_runs, 1))
            self._restart_spinbox.setValue(configuration.restart_from_model or 0)
            self._mpi_tasks_spinbox.setValue(configuration.mpi_tasks or 0)
            self._geometry_fixed_checkbox.setChecked(configuration.geometry_fixed)
            self._write_processed_checkbox.setChecked(configuration.write_processed)
            self._benchmark_checkbox.setChecked(configuration.benchmark)
            self._mpi_no_spawn_checkbox.setChecked(configuration.mpi_no_spawn)
            self._extra_args_edit.setText(" ".join(configuration.extra_arguments))

        self._refresh_configuration_summary()

    def set_runtime_label(self, runtime_label: str) -> None:
        self._runtime_label.setText(runtime_label)
        self._readiness_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.readiness"),
            value=self._readiness_state_label.text(),
            caption=runtime_label,
        )

    def set_project_state(self, *, project_name: str | None, is_dirty: bool) -> None:
        if project_name is None:
            self._has_project = False
            self._project_state_label.setText(self._localization.text("simulation.no_project"))
            self._activity_tile.set_content(
                eyebrow=self._localization.text("simulation.metric.activity"),
                value=self._project_state_label.text(),
            )
            self._update_action_state()
            return
        self._has_project = True
        dirty_state = self._localization.text(
            "simulation.project_state.dirty" if is_dirty else "simulation.project_state.saved"
        )
        self._project_state_label.setText(
            self._localization.text(
                "simulation.project_state",
                name=project_name,
                state=dirty_state,
            )
        )
        self._activity_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.activity"),
            value=self._project_state_label.text(),
        )
        self._update_action_state()

    def set_validation_messages(self, messages: list[str]) -> None:
        if not messages:
            self._validation_label.setText(
                self._localization.text("simulation.validation_placeholder")
            )
            return
        self._validation_label.setText("\n".join(messages))

    def set_readiness_state(
        self,
        *,
        summary: str,
        caption: str = "",
        start_allowed: bool,
    ) -> None:
        self._readiness_state_label.setText(summary)
        self._start_allowed = start_allowed
        self._readiness_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.readiness"),
            value=summary,
            caption=caption or self._runtime_label.text(),
        )
        self._update_action_state()

    def set_input_preview(self, preview_text: str) -> None:
        self._preview_text.setPlainText(preview_text)

    def set_log_output(self, log_text: str) -> None:
        if self._log_text.toPlainText() == log_text:
            return
        self._log_text.setPlainText(log_text)
        cursor = self._log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log_text.setTextCursor(cursor)

    def set_run_state(
        self,
        active_run: SimulationRunRecord | None,
        history: list[SimulationRunRecord],
    ) -> None:
        signature = (
            active_run.run_id if active_run is not None else None,
            active_run.status.value if active_run is not None else None,
            active_run.error_summary if active_run is not None else None,
            tuple(
                (run.run_id, run.status.value, run.created_at.isoformat())
                for run in history
            ),
        )
        if active_run is None:
            self._status_label.setText(
                self._localization.text("simulation.run_state.none")
            )
            self._run_in_progress = False
        else:
            status_text = self._localization.text(
                "simulation.run_state.active",
                run_id=active_run.run_id,
                status=self._localization.simulation_status_text(
                    active_run.status.value
                ),
            )
            if active_run.error_summary and active_run.status.value in {"failed", "cancelled"}:
                status_text = f"{status_text} | {active_run.error_summary}"
            self._status_label.setText(status_text)
            self._run_in_progress = active_run.status.value in {"preparing", "running"}
        self._activity_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.activity"),
            value=self._status_label.text(),
        )

        if self._run_state_signature == signature:
            self._has_retry_target = bool(history)
            self._update_action_state()
            return

        current_selection = self.selected_run_id()
        self._run_history.clear()
        for run in history:
            item = QListWidgetItem(
                f"{run.run_id} | "
                f"{self._localization.simulation_status_text(run.status.value)} | "
                f"{run.created_at.isoformat()}"
            )
            item.setData(Qt.ItemDataRole.UserRole, run.run_id)
            self._run_history.addItem(item)
            if current_selection and current_selection == run.run_id:
                self._run_history.setCurrentItem(item)
        if self._run_history.currentItem() is None and self._run_history.count() > 0:
            self._run_history.setCurrentRow(0)
        self._has_retry_target = bool(history)
        self._run_state_signature = signature
        self._update_action_state()

    def selected_run_id(self) -> str | None:
        item = self._run_history.currentItem()
        if item is None:
            return None
        data = item.data(Qt.ItemDataRole.UserRole)
        return data if isinstance(data, str) else None

    def _build_runtime_widget(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        self._runtime_row_label = QLabel()
        self._readiness_row_label = QLabel()
        self._project_state_row_label = QLabel()
        self._run_state_row_label = QLabel()
        self._messages_row_label = QLabel()
        layout.addRow(self._runtime_row_label, self._runtime_label)
        layout.addRow(self._readiness_row_label, self._readiness_state_label)
        layout.addRow(self._project_state_row_label, self._project_state_label)
        layout.addRow(self._run_state_row_label, self._status_label)
        layout.addRow(self._messages_row_label, self._validation_label)
        return widget

    def _build_config_widget(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        self._config_form = layout
        self._mode_label = QLabel()
        self._num_runs_label = QLabel()
        self._restart_label = QLabel()
        self._mpi_tasks_label = QLabel()
        self._extra_args_label = QLabel()
        layout.addRow(self._mode_label, self._mode_combo)
        layout.addRow(self._num_runs_label, self._num_runs_spinbox)
        layout.addRow(self._restart_label, self._restart_spinbox)
        layout.addRow(self._mpi_tasks_label, self._mpi_tasks_spinbox)
        layout.addRow("", self._geometry_fixed_checkbox)
        layout.addRow("", self._write_processed_checkbox)
        layout.addRow("", self._benchmark_checkbox)
        layout.addRow("", self._mpi_no_spawn_checkbox)
        layout.addRow(self._extra_args_label, self._extra_args_edit)
        return widget

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_responsive_layout()

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

    def _parse_int_list(self, raw: str) -> list[int]:
        cleaned = raw.replace(",", " ").strip()
        if not cleaned:
            return []
        values: list[int] = []
        for item in cleaned.split():
            try:
                values.append(int(item))
            except ValueError:
                continue
        return values

    def retranslate_ui(self) -> None:
        self._title.setText(self._localization.text("simulation.title"))
        self._subtitle.setText(self._localization.text("simulation.subtitle"))
        self._nav_heading.setText(self._localization.text("simulation.navigation"))
        self._retranslate_sections()
        self._mode_combo.setItemText(
            0, self._localization.simulation_mode_text(SimulationMode.NORMAL.value)
        )
        self._mode_combo.setItemText(
            1,
            self._localization.simulation_mode_text(
                SimulationMode.GEOMETRY_ONLY.value
            ),
        )
        self._geometry_fixed_checkbox.setText(
            self._localization.text("simulation.geometry_fixed")
        )
        self._write_processed_checkbox.setText(
            self._localization.text("simulation.write_processed")
        )
        self._benchmark_checkbox.setText(
            self._localization.text("simulation.benchmark")
        )
        self._mpi_no_spawn_checkbox.setText(
            self._localization.text("simulation.mpi_no_spawn")
        )
        self._extra_args_edit.setPlaceholderText(
            self._localization.text("simulation.extra_args_placeholder")
        )
        self._preview_text.setPlaceholderText(
            self._localization.text("simulation.preview_placeholder")
        )
        self._log_text.setPlaceholderText(
            self._localization.text("simulation.log_placeholder")
        )
        self._preview_button.setText(
            self._localization.text("simulation.action.preview")
        )
        self._export_button.setText(
            self._localization.text("simulation.action.export")
        )
        self._start_button.setText(self._localization.text("simulation.action.start"))
        self._retry_button.setText(self._localization.text("simulation.action.retry"))
        self._cancel_button.setText(
            self._localization.text("simulation.action.cancel")
        )
        self._open_run_button.setText(
            self._localization.text("simulation.action.open_run")
        )
        self._open_output_button.setText(
            self._localization.text("simulation.action.open_output")
        )
        self._runtime_row_label.setText(self._localization.text("simulation.runtime"))
        self._readiness_row_label.setText(
            self._localization.text("simulation.readiness_label")
        )
        self._project_state_row_label.setText(
            self._localization.text("simulation.project_state_label")
        )
        self._run_state_row_label.setText(
            self._localization.text("simulation.run_state_label")
        )
        self._messages_row_label.setText(
            self._localization.text("simulation.messages")
        )
        self._mode_label.setText(self._localization.text("simulation.mode"))
        self._num_runs_label.setText(self._localization.text("simulation.num_runs"))
        self._restart_label.setText(self._localization.text("simulation.restart"))
        self._mpi_tasks_label.setText(self._localization.text("simulation.mpi_tasks"))
        self._extra_args_label.setText(self._localization.text("simulation.extra_args"))
        for key, heading in self._card_headings.items():
            heading.setText(self._localization.text(key))
        self._refresh_configuration_summary()
        self._refresh_section_selection()
        self._update_advanced_rows()

    def set_advanced_mode(self, enabled: bool) -> None:
        if self._advanced_mode == enabled:
            return
        self._advanced_mode = enabled
        self._update_advanced_rows()

    def ui_state(self) -> dict[str, object]:
        state: dict[str, object] = {
            "top_splitter": self._splitter_state(self._top_splitter),
            "content_splitter": self._splitter_state(self._content_splitter),
        }
        current_key = self._current_section_key()
        if current_key is not None:
            state["section_key"] = current_key
        return state

    def apply_ui_state(self, state: dict[str, object] | None) -> None:
        if not isinstance(state, dict):
            return
        section_key = state.get("section_key")
        self._pending_section_key = section_key if isinstance(section_key, str) else None
        top_state = state.get("top_splitter")
        if isinstance(top_state, dict):
            self._persisted_top_splitter = top_state
        content_state = state.get("content_splitter")
        if isinstance(content_state, dict):
            self._persisted_content_splitter = content_state
        self._refresh_section_selection()
        self._refresh_responsive_layout(force=True)

    def _refresh_configuration_summary(self) -> None:
        self._readiness_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.readiness"),
            value=self._readiness_state_label.text(),
            caption=self._runtime_label.text(),
        )
        self._mode_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.mode"),
            value=self._localization.simulation_mode_text(
                self._mode_combo.currentData() or SimulationMode.NORMAL.value
            ),
        )
        self._runs_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.runs"),
            value=str(self._num_runs_spinbox.value()),
        )

        activity_value = self._status_label.text() or self._project_state_label.text()
        self._activity_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.activity"),
            value=activity_value,
        )

    def _on_configuration_widget_changed(self, *_args) -> None:
        self._refresh_configuration_summary()
        self.configuration_changed.emit()

    def _update_action_state(self) -> None:
        has_selected_run = self.selected_run_id() is not None
        launch_available = self._has_project and not self._run_in_progress
        self._start_button.setEnabled(
            self._has_project and self._start_allowed and not self._run_in_progress
        )
        self._preview_button.setEnabled(launch_available)
        self._export_button.setEnabled(launch_available)
        self._cancel_button.setEnabled(self._run_in_progress)
        self._retry_button.setEnabled(self._has_retry_target and not self._run_in_progress)
        self._open_run_button.setEnabled(has_selected_run)
        self._open_output_button.setEnabled(has_selected_run)

    def _refresh_responsive_layout(self, *, force: bool = False) -> None:
        wide = self.width() >= 1020
        top_orientation = Qt.Orientation.Horizontal if wide else Qt.Orientation.Vertical
        top_orientation_changed = self._top_splitter.orientation() != top_orientation
        if top_orientation_changed:
            self._top_splitter.setOrientation(top_orientation)
            self._top_splitter_user_resized = False
        if force or top_orientation_changed or not self._top_splitter_user_resized:
            persisted_top = self._splitter_sizes_for_orientation(
                self._persisted_top_splitter,
                top_orientation,
            )
            if persisted_top is not None:
                self._apply_splitter_sizes(self._top_splitter, persisted_top)
            elif wide:
                left_width = max(360, min(520, int(self.width() * 0.42)))
                self._apply_splitter_sizes(
                    self._top_splitter,
                    [left_width, max(420, self.width() - left_width)],
                )
            else:
                top_height = 260 if self.height() >= 720 else 220
                self._apply_splitter_sizes(
                    self._top_splitter,
                    [top_height, max(340, self.height() - top_height)],
                )

        content_orientation = (
            Qt.Orientation.Horizontal
            if self.width() >= 980
            else Qt.Orientation.Vertical
        )
        content_orientation_changed = (
            self._content_splitter.orientation() != content_orientation
        )
        if content_orientation_changed:
            self._content_splitter.setOrientation(content_orientation)
            self._content_splitter_user_resized = False
        if force or content_orientation_changed or not self._content_splitter_user_resized:
            persisted_content = self._splitter_sizes_for_orientation(
                self._persisted_content_splitter,
                content_orientation,
            )
            if persisted_content is not None:
                self._apply_splitter_sizes(self._content_splitter, persisted_content)
                return
            if content_orientation == Qt.Orientation.Horizontal:
                nav_width = max(210, min(250, int(self.width() * 0.22)))
                self._apply_splitter_sizes(
                    self._content_splitter,
                    [nav_width, max(640, self.width() - nav_width)],
                )
                return
            top_height = 170 if self.height() >= 700 else 146
            self._apply_splitter_sizes(
                self._content_splitter,
                [top_height, max(360, self.height() - top_height)],
            )
            return

    def _apply_splitter_sizes(self, splitter: QSplitter, sizes: list[int]) -> None:
        self._syncing_splitter_sizes = True
        try:
            splitter.setSizes(sizes)
        finally:
            self._syncing_splitter_sizes = False

    def _on_top_splitter_moved(self, _pos: int, _index: int) -> None:
        if self._syncing_splitter_sizes:
            return
        self._top_splitter_user_resized = True

    def _on_content_splitter_moved(self, _pos: int, _index: int) -> None:
        if self._syncing_splitter_sizes:
            return
        self._content_splitter_user_resized = True

    def _retranslate_sections(self) -> None:
        current_key = self._current_section_key() or self._pending_section_key
        self._section_nav.clear()
        for index, title_key in enumerate(self._sections):
            item = QListWidgetItem(self._localization.text(title_key))
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setData(Qt.ItemDataRole.UserRole + 1, title_key)
            self._section_nav.addItem(item)
        row = self._row_for_section_key(current_key)
        if row < 0 and self._section_nav.count() > 0:
            row = 0
        if row >= 0:
            self._section_nav.setCurrentRow(row)

    def _on_section_changed(self, row: int) -> None:
        if row < 0:
            return
        item = self._section_nav.item(row)
        self._pending_section_key = (
            item.data(Qt.ItemDataRole.UserRole + 1)
            if item is not None
            else self._pending_section_key
        )
        self._section_stack.setCurrentIndex(row)

    def _refresh_section_selection(self) -> None:
        row = self._row_for_section_key(self._pending_section_key)
        if row < 0 and self._section_nav.count() > 0:
            row = min(self._section_nav.currentRow(), self._section_nav.count() - 1)
        if row >= 0:
            self._section_nav.setCurrentRow(row)

    def _update_advanced_rows(self) -> None:
        if not hasattr(self, "_config_form"):
            return
        advanced_rows = (
            self._restart_spinbox,
            self._mpi_tasks_spinbox,
            self._benchmark_checkbox,
            self._mpi_no_spawn_checkbox,
            self._extra_args_edit,
        )
        for widget in advanced_rows:
            self._config_form.setRowVisible(widget, self._advanced_mode)

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
        state: dict[str, object] | None,
        orientation: Qt.Orientation,
    ) -> list[int] | None:
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
