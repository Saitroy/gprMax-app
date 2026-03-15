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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...domain.execution_status import SimulationMode
from ...domain.gprmax_config import SimulationRunConfig
from ...domain.simulation import SimulationRunRecord


class SimulationView(QWidget):
    preview_requested = Signal()
    export_requested = Signal()
    start_requested = Signal()
    cancel_requested = Signal()
    open_run_directory_requested = Signal()
    open_output_directory_requested = Signal()

    def __init__(self, runtime_label: str, parent=None) -> None:
        super().__init__(parent)

        title = QLabel("Simulation Runner")
        title.setObjectName("ViewTitle")

        subtitle = QLabel(
            "Stage 3 adds input generation, subprocess execution, live logs, and run "
            "history. The current screen intentionally focuses on reliable execution flow."
        )
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        self._runtime_label = QLabel(runtime_label)
        self._project_state_label = QLabel("No project loaded.")
        self._status_label = QLabel("No run prepared.")
        self._validation_label = QLabel("Validation messages will appear here.")
        self._validation_label.setWordWrap(True)

        self._mode_combo = QComboBox()
        self._mode_combo.addItem("Normal run", SimulationMode.NORMAL.value)
        self._mode_combo.addItem("Geometry-only", SimulationMode.GEOMETRY_ONLY.value)

        self._gpu_checkbox = QCheckBox("Use GPU")
        self._gpu_devices_edit = QLineEdit()
        self._gpu_devices_edit.setPlaceholderText("Optional device IDs, e.g. 0 1")

        self._num_runs_spinbox = QSpinBox()
        self._num_runs_spinbox.setRange(1, 1_000_000)
        self._num_runs_spinbox.setValue(1)

        self._restart_spinbox = QSpinBox()
        self._restart_spinbox.setRange(0, 1_000_000)
        self._restart_spinbox.setValue(0)

        self._mpi_tasks_spinbox = QSpinBox()
        self._mpi_tasks_spinbox.setRange(0, 4096)
        self._mpi_tasks_spinbox.setValue(0)

        self._geometry_fixed_checkbox = QCheckBox("Geometry fixed")
        self._write_processed_checkbox = QCheckBox("Write processed input")
        self._benchmark_checkbox = QCheckBox("Benchmark mode")
        self._mpi_no_spawn_checkbox = QCheckBox("MPI no spawn")
        self._extra_args_edit = QLineEdit()
        self._extra_args_edit.setPlaceholderText("Optional raw CLI args")

        self._preview_text = QPlainTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setPlaceholderText("Generated gprMax input preview")

        self._log_text = QPlainTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setPlaceholderText("Live stdout/stderr output")

        self._run_history = QListWidget()

        preview_button = QPushButton("Build Preview")
        preview_button.clicked.connect(self.preview_requested.emit)

        export_button = QPushButton("Export Input")
        export_button.clicked.connect(self.export_requested.emit)

        start_button = QPushButton("Start Run")
        start_button.clicked.connect(self.start_requested.emit)
        self._start_button = start_button

        cancel_button = QPushButton("Cancel Run")
        cancel_button.clicked.connect(self.cancel_requested.emit)
        self._cancel_button = cancel_button

        open_run_button = QPushButton("Open Run Folder")
        open_run_button.clicked.connect(self.open_run_directory_requested.emit)

        open_output_button = QPushButton("Open Output Folder")
        open_output_button.clicked.connect(self.open_output_directory_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(preview_button)
        buttons.addWidget(export_button)
        buttons.addWidget(start_button)
        buttons.addWidget(cancel_button)
        buttons.addWidget(open_run_button)
        buttons.addWidget(open_output_button)
        buttons.addStretch(1)

        runtime_card = self._build_card(
            "Execution context",
            self._build_runtime_widget(),
        )
        config_card = self._build_card("Run configuration", self._build_config_widget())
        history_card = self._build_card("Run history", self._run_history)

        io_layout = QGridLayout()
        io_layout.addWidget(self._build_card("Input preview", self._preview_text), 0, 0)
        io_layout.addWidget(self._build_card("Live log output", self._log_text), 0, 1)
        io_layout.setColumnStretch(0, 1)
        io_layout.setColumnStretch(1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(runtime_card)
        layout.addWidget(config_card)
        layout.addLayout(buttons)
        layout.addLayout(io_layout)
        layout.addWidget(history_card, 1)

        self.set_run_state(None, [])
        self.set_project_state(project_name=None, is_dirty=False)

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

    def set_project_state(self, *, project_name: str | None, is_dirty: bool) -> None:
        if project_name is None:
            self._project_state_label.setText("No project loaded.")
            return
        dirty_state = "unsaved changes" if is_dirty else "saved"
        self._project_state_label.setText(
            f"Project: {project_name} ({dirty_state})"
        )

    def set_validation_messages(self, messages: list[str]) -> None:
        if not messages:
            self._validation_label.setText("Validation messages will appear here.")
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
            self._status_label.setText("No active run.")
            self._cancel_button.setEnabled(False)
            self._start_button.setEnabled(True)
        else:
            self._status_label.setText(
                f"Run {active_run.run_id}: {active_run.status.value}"
            )
            is_running = active_run.status.value in {"preparing", "running"}
            self._cancel_button.setEnabled(is_running)
            self._start_button.setEnabled(not is_running)

        current_selection = self.selected_run_id()
        self._run_history.clear()
        for run in history:
            item = QListWidgetItem(
                f"{run.run_id} | {run.status.value} | {run.created_at.isoformat()}"
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
        layout.addRow("Runtime", self._runtime_label)
        layout.addRow("Project state", self._project_state_label)
        layout.addRow("Run state", self._status_label)
        layout.addRow("Messages", self._validation_label)
        return widget

    def _build_config_widget(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.addRow("Mode", self._mode_combo)
        layout.addRow("", self._gpu_checkbox)
        layout.addRow("GPU device IDs", self._gpu_devices_edit)
        layout.addRow("Model runs (-n)", self._num_runs_spinbox)
        layout.addRow("Restart model (-restart)", self._restart_spinbox)
        layout.addRow("MPI tasks (-mpi)", self._mpi_tasks_spinbox)
        layout.addRow("", self._geometry_fixed_checkbox)
        layout.addRow("", self._write_processed_checkbox)
        layout.addRow("", self._benchmark_checkbox)
        layout.addRow("", self._mpi_no_spawn_checkbox)
        layout.addRow("Extra CLI args", self._extra_args_edit)
        return widget

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
