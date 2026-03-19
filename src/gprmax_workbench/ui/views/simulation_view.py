from __future__ import annotations

import shlex

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...application.services.localization_service import LocalizationService
from ...domain.execution_status import SimulationMode
from ...domain.gprmax_config import SimulationRunConfig
from ...domain.simulation import SimulationRunRecord
from ..layouts.flow_layout import FlowLayout
from ..widgets.metric_tile import MetricTile


class SimulationView(QWidget):
    preview_requested = Signal()
    export_requested = Signal()
    start_requested = Signal()
    cancel_requested = Signal()
    open_run_directory_requested = Signal()
    open_output_directory_requested = Signal()

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

        self._title = QLabel()
        self._title.setObjectName("ViewTitle")

        self._subtitle = QLabel()
        self._subtitle.setObjectName("ViewSubtitle")
        self._subtitle.setWordWrap(True)

        self._runtime_label = QLabel(runtime_label)
        self._project_state_label = QLabel()
        self._status_label = QLabel()
        self._validation_label = QLabel()
        self._validation_label.setWordWrap(True)

        self._mode_tile = MetricTile()
        self._runs_tile = MetricTile()
        self._runtime_tile = MetricTile()
        self._activity_tile = MetricTile()

        self._mode_combo = QComboBox()
        self._mode_combo.addItem("", SimulationMode.NORMAL.value)
        self._mode_combo.addItem("", SimulationMode.GEOMETRY_ONLY.value)
        self._mode_combo.currentIndexChanged.connect(self._refresh_configuration_summary)

        self._gpu_checkbox = QCheckBox()
        self._gpu_devices_edit = QLineEdit()
        self._gpu_devices_edit.setPlaceholderText("")

        self._num_runs_spinbox = QSpinBox()
        self._num_runs_spinbox.setRange(1, 1_000_000)
        self._num_runs_spinbox.setValue(1)
        self._num_runs_spinbox.valueChanged.connect(self._refresh_configuration_summary)

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

        self._preview_text = QPlainTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setPlaceholderText("")

        self._log_text = QPlainTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setPlaceholderText("")

        self._run_history = QListWidget()

        self._preview_button = QPushButton()
        self._preview_button.clicked.connect(self.preview_requested.emit)

        self._export_button = QPushButton()
        self._export_button.clicked.connect(self.export_requested.emit)

        self._start_button = QPushButton()
        self._start_button.setObjectName("PrimaryButton")
        self._start_button.clicked.connect(self.start_requested.emit)

        self._cancel_button = QPushButton()
        self._cancel_button.clicked.connect(self.cancel_requested.emit)

        self._open_run_button = QPushButton()
        self._open_run_button.clicked.connect(self.open_run_directory_requested.emit)

        self._open_output_button = QPushButton()
        self._open_output_button.clicked.connect(self.open_output_directory_requested.emit)

        buttons = FlowLayout(horizontal_spacing=10, vertical_spacing=10)
        buttons.addWidget(self._start_button)
        buttons.addWidget(self._preview_button)
        buttons.addWidget(self._export_button)
        buttons.addWidget(self._cancel_button)
        buttons.addWidget(self._open_run_button)
        buttons.addWidget(self._open_output_button)

        metrics_row = FlowLayout(horizontal_spacing=12, vertical_spacing=12)
        metrics_row.addWidget(self._mode_tile)
        metrics_row.addWidget(self._runs_tile)
        metrics_row.addWidget(self._runtime_tile)
        metrics_row.addWidget(self._activity_tile)

        runtime_card = self._build_card(
            "simulation.runtime_card",
            self._build_runtime_widget(),
        )
        config_card = self._build_card(
            "simulation.config_card",
            self._build_config_widget(),
        )
        history_card = self._build_card("simulation.history_card", self._run_history)

        self._top_splitter = QSplitter()
        self._top_splitter.addWidget(runtime_card)
        self._top_splitter.addWidget(config_card)
        self._top_splitter.setStretchFactor(0, 1)
        self._top_splitter.setStretchFactor(1, 1)
        self._top_splitter.setChildrenCollapsible(False)

        self._io_splitter = QSplitter()
        self._io_splitter.addWidget(
            self._build_card("simulation.preview_card", self._preview_text),
        )
        self._io_splitter.addWidget(
            self._build_card("simulation.log_card", self._log_text),
        )
        self._io_splitter.setStretchFactor(0, 1)
        self._io_splitter.setStretchFactor(1, 1)
        self._io_splitter.setChildrenCollapsible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addLayout(metrics_row)
        layout.addWidget(self._top_splitter)
        layout.addLayout(buttons)
        layout.addWidget(self._io_splitter)
        layout.addWidget(history_card, 1)

        self.retranslate_ui()
        self.set_run_state(None, [])
        self.set_project_state(project_name=None, is_dirty=False)
        self._refresh_configuration_summary()
        self._refresh_responsive_layout()

    def current_configuration(self) -> SimulationRunConfig:
        mode = SimulationMode(self._mode_combo.currentData())
        gpu_devices = self._parse_int_list(self._gpu_devices_edit.text())
        restart_from = self._restart_spinbox.value() or None
        mpi_tasks = self._mpi_tasks_spinbox.value() or None
        extra_arguments = (
            shlex.split(self._extra_args_edit.text(), posix=False)
            if self._extra_args_edit.text().strip()
            else []
        )

        return SimulationRunConfig(
            mode=mode,
            use_gpu=self._gpu_checkbox.isChecked(),
            gpu_device_ids=gpu_devices,
            benchmark=self._benchmark_checkbox.isChecked(),
            geometry_fixed=self._geometry_fixed_checkbox.isChecked(),
            write_processed=self._write_processed_checkbox.isChecked(),
            num_model_runs=self._num_runs_spinbox.value(),
            restart_from_model=restart_from,
            mpi_tasks=mpi_tasks,
            mpi_no_spawn=self._mpi_no_spawn_checkbox.isChecked(),
            extra_arguments=extra_arguments,
        )

    def set_runtime_label(self, runtime_label: str) -> None:
        self._runtime_label.setText(runtime_label)
        self._refresh_configuration_summary()

    def set_project_state(self, *, project_name: str | None, is_dirty: bool) -> None:
        if project_name is None:
            self._project_state_label.setText(self._localization.text("simulation.no_project"))
            return
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

    def set_validation_messages(self, messages: list[str]) -> None:
        if not messages:
            self._validation_label.setText(
                self._localization.text("simulation.validation_placeholder")
            )
            return
        self._validation_label.setText("\n".join(messages))

    def set_input_preview(self, preview_text: str) -> None:
        self._preview_text.setPlainText(preview_text)

    def set_log_output(self, log_text: str) -> None:
        self._log_text.setPlainText(log_text)
        cursor = self._log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log_text.setTextCursor(cursor)

    def set_run_state(
        self,
        active_run: SimulationRunRecord | None,
        history: list[SimulationRunRecord],
    ) -> None:
        if active_run is None:
            self._status_label.setText(
                self._localization.text("simulation.run_state.none")
            )
            self._cancel_button.setEnabled(False)
            self._start_button.setEnabled(True)
        else:
            self._status_label.setText(
                self._localization.text(
                    "simulation.run_state.active",
                    run_id=active_run.run_id,
                    status=self._localization.simulation_status_text(
                        active_run.status.value
                    ),
                )
            )
            is_running = active_run.status.value in {"preparing", "running"}
            self._cancel_button.setEnabled(is_running)
            self._start_button.setEnabled(not is_running)
        self._activity_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.activity"),
            value=self._status_label.text(),
        )

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
        self._project_state_row_label = QLabel()
        self._run_state_row_label = QLabel()
        self._messages_row_label = QLabel()
        layout.addRow(self._runtime_row_label, self._runtime_label)
        layout.addRow(self._project_state_row_label, self._project_state_label)
        layout.addRow(self._run_state_row_label, self._status_label)
        layout.addRow(self._messages_row_label, self._validation_label)
        return widget

    def _build_config_widget(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        self._mode_label = QLabel()
        self._gpu_devices_label = QLabel()
        self._num_runs_label = QLabel()
        self._restart_label = QLabel()
        self._mpi_tasks_label = QLabel()
        self._extra_args_label = QLabel()
        layout.addRow(self._mode_label, self._mode_combo)
        layout.addRow("", self._gpu_checkbox)
        layout.addRow(self._gpu_devices_label, self._gpu_devices_edit)
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
        self._mode_combo.setItemText(
            0, self._localization.simulation_mode_text(SimulationMode.NORMAL.value)
        )
        self._mode_combo.setItemText(
            1,
            self._localization.simulation_mode_text(
                SimulationMode.GEOMETRY_ONLY.value
            ),
        )
        self._gpu_checkbox.setText(self._localization.text("simulation.gpu"))
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
        self._gpu_devices_edit.setPlaceholderText(
            self._localization.text("simulation.gpu_devices_placeholder")
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
        self._gpu_devices_label.setText(
            self._localization.text("simulation.gpu_devices")
        )
        self._num_runs_label.setText(self._localization.text("simulation.num_runs"))
        self._restart_label.setText(self._localization.text("simulation.restart"))
        self._mpi_tasks_label.setText(self._localization.text("simulation.mpi_tasks"))
        self._extra_args_label.setText(self._localization.text("simulation.extra_args"))
        for key, heading in self._card_headings.items():
            heading.setText(self._localization.text(key))
        self._refresh_configuration_summary()

    def _refresh_configuration_summary(self) -> None:
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
        self._runtime_tile.set_content(
            eyebrow=self._localization.text("simulation.metric.runtime"),
            value=self._runtime_label.text() or self._localization.text("common.not_set"),
        )

    def _refresh_responsive_layout(self) -> None:
        wide = self.width() >= 1120
        top_orientation = Qt.Orientation.Horizontal if wide else Qt.Orientation.Vertical
        io_orientation = Qt.Orientation.Horizontal if self.width() >= 1240 else Qt.Orientation.Vertical
        self._top_splitter.setOrientation(top_orientation)
        self._io_splitter.setOrientation(io_orientation)
