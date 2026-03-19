from __future__ import annotations

from math import isclose

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy, QStackedLayout, QWidget

from ....application.services.localization_service import LocalizationService
from ....domain.traces import AscanTrace


class TracePlotWidget(QWidget):
    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._chart = QChart()
        self._chart.legend().setVisible(True)
        self._chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self._chart.setTitle("")
        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._chart_view.setMinimumHeight(320)
        self._chart_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._message = QLabel()
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setWordWrap(True)
        self._message.setMinimumHeight(320)
        self._message.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        layout = QStackedLayout(self)
        layout.addWidget(self._message)
        layout.addWidget(self._chart_view)
        layout.setCurrentWidget(self._message)
        self._layout = layout
        self.retranslate_ui()

    def clear(self, message: str) -> None:
        self._message.setText(message)
        self._layout.setCurrentWidget(self._message)

    def set_trace(self, trace: AscanTrace) -> None:
        self.set_traces([trace])

    def set_traces(self, traces: list[AscanTrace]) -> None:
        if not traces:
            self.clear(self._localization.text("results.plot.ascan_prompt"))
            return

        self._chart.removeAllSeries()
        for axis in self._chart.axes():
            self._chart.removeAxis(axis)

        x_axis = QValueAxis()
        x_axis.setTitleText(self._localization.text("results.plot.time_ns"))
        x_axis.setLabelFormat("%.3g")
        y_axis = QValueAxis()
        y_axis.setTitleText(self._localization.text("results.plot.amplitude"))
        y_axis.setLabelFormat("%.3g")

        self._chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        palette = [
            QColor("#4d7c99"),
            QColor("#a65d57"),
            QColor("#5f8f63"),
            QColor("#8a6aa6"),
            QColor("#b07b32"),
            QColor("#4f6fa8"),
        ]
        x_values_ns: list[float] = []
        y_values: list[float] = []
        for index, trace in enumerate(traces):
            series = QLineSeries()
            series.setName(trace.metadata.component)
            series.setColor(palette[index % len(palette)])
            series.append(
                [
                    QPointF(time_s * 1e9, value)
                    for time_s, value in zip(trace.time_s, trace.values)
                ]
            )
            self._chart.addSeries(series)
            series.attachAxis(x_axis)
            series.attachAxis(y_axis)
            x_values_ns.extend(time_s * 1e9 for time_s in trace.time_s)
            y_values.extend(trace.values)

        if x_values_ns:
            x_min = min(x_values_ns)
            x_max = max(x_values_ns)
            if isclose(x_min, x_max):
                x_max = x_min + 1.0
            x_axis.setRange(x_min, x_max)
        if y_values:
            y_min = min(y_values)
            y_max = max(y_values)
            if isclose(y_min, y_max):
                padding = abs(y_min) * 0.05 or 1.0
                y_min -= padding
                y_max += padding
            else:
                padding = (y_max - y_min) * 0.05
                y_min -= padding
                y_max += padding
            y_axis.setRange(y_min, y_max)

        receiver_name = traces[0].metadata.receiver_name
        component_label = ", ".join(trace.metadata.component for trace in traces)
        self._chart.setTitle(
            self._localization.text(
                "results.plot.ascan_chart_title",
                receiver_name=receiver_name,
                component=component_label,
            )
        )
        self._layout.setCurrentWidget(self._chart_view)

    def retranslate_ui(self) -> None:
        self._chart.setTitle(self._localization.text("results.plot.ascan_title"))
        self._message.setText(self._localization.text("results.plot.ascan_prompt"))
