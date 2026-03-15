from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from ....application.services.localization_service import LocalizationService
from ....domain.results import ResultMetadata, RunResultSummary


class ResultSummaryPanel(QWidget):
    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization

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
        self._labels = {
            "run_id": QLabel(),
            "status": QLabel(),
            "created": QLabel(),
            "finished": QLabel(),
            "duration": QLabel(),
            "input_file": QLabel(),
            "output_file": QLabel(),
            "model_title": QLabel(),
            "receivers": QLabel(),
            "components": QLabel(),
            "grid": QLabel(),
            "dt": QLabel(),
            "notes": QLabel(),
        }
        form.addRow(self._labels["run_id"], self._run_id)
        form.addRow(self._labels["status"], self._status)
        form.addRow(self._labels["created"], self._created)
        form.addRow(self._labels["finished"], self._finished)
        form.addRow(self._labels["duration"], self._duration)
        form.addRow(self._labels["input_file"], self._input_file)
        form.addRow(self._labels["output_file"], self._output_file)
        form.addRow(self._labels["model_title"], self._model_title)
        form.addRow(self._labels["receivers"], self._receivers)
        form.addRow(self._labels["components"], self._components)
        form.addRow(self._labels["grid"], self._grid)
        form.addRow(self._labels["dt"], self._dt)
        form.addRow(self._labels["notes"], self._issues)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        self.retranslate_ui()

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
            self._issues.setText(self._localization.text("results.summary.select_run"))
            return

        record = run_summary.run_record
        self._run_id.setText(record.run_id)
        self._status.setText(
            self._localization.simulation_status_text(record.status.value)
        )
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
        self._issues.setText(
            "\n".join(
                self._localization.translate_message(issue)
                for issue in run_summary.issues
            )
            if run_summary.issues
            else self._localization.text("results.summary.no_issues")
        )

    def retranslate_ui(self) -> None:
        for key, label in self._labels.items():
            label.setText(self._localization.text(f"results.summary.{key}"))


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.isoformat(sep=" ", timespec="seconds")
