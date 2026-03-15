from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from ....domain.results import ResultMetadata, RunResultSummary


class ResultSummaryPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._run_id = QLabel("-")
        self._status = QLabel("-")
        self._created = QLabel("-")
        self._finished = QLabel("-")
        self._duration = QLabel("-")
        self._input_file = QLabel("-")
        self._output_file = QLabel("-")
        self._model_title = QLabel("-")
        self._receivers = QLabel("-")
        self._components = QLabel("-")
        self._grid = QLabel("-")
        self._dt = QLabel("-")
        self._issues = QLabel("-")
        self._issues.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Run ID", self._run_id)
        form.addRow("Status", self._status)
        form.addRow("Created", self._created)
        form.addRow("Finished", self._finished)
        form.addRow("Duration", self._duration)
        form.addRow("Input file", self._input_file)
        form.addRow("Output file", self._output_file)
        form.addRow("Model title", self._model_title)
        form.addRow("Receivers", self._receivers)
        form.addRow("Components", self._components)
        form.addRow("Grid", self._grid)
        form.addRow("dt", self._dt)
        form.addRow("Notes", self._issues)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)

    def set_summary(
        self,
        run_summary: RunResultSummary | None,
        metadata: ResultMetadata | None,
    ) -> None:
        if run_summary is None:
            for label in (
                self._run_id,
                self._status,
                self._created,
                self._finished,
                self._duration,
                self._input_file,
                self._output_file,
                self._model_title,
                self._receivers,
                self._components,
                self._grid,
                self._dt,
            ):
                label.setText("-")
            self._issues.setText("Select a completed run to inspect results.")
            return

        record = run_summary.run_record
        self._run_id.setText(record.run_id)
        self._status.setText(record.status.value)
        self._created.setText(_format_dt(record.created_at))
        self._finished.setText(_format_dt(record.finished_at))
        self._duration.setText(
            f"{record.duration_seconds:.3f} s"
            if record.duration_seconds is not None
            else "-"
        )
        self._input_file.setText(str(record.input_file))
        self._output_file.setText(str(metadata.output_file.path) if metadata else "-")
        self._model_title.setText(metadata.model_title if metadata and metadata.model_title else "-")
        self._receivers.setText(
            str(metadata.receiver_count) if metadata is not None else "-"
        )
        self._components.setText(
            ", ".join(metadata.available_components) if metadata and metadata.available_components else "-"
        )
        self._grid.setText(
            " x ".join(str(item) for item in metadata.grid_shape) if metadata else "-"
        )
        self._dt.setText(f"{metadata.dt_s:.6g} s" if metadata else "-")
        self._issues.setText("\n".join(run_summary.issues) if run_summary.issues else "No result issues detected.")


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.isoformat(sep=" ", timespec="seconds")
