from __future__ import annotations

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel, QStackedLayout, QWidget

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
        self._chart.legend().hide()
        self._chart.setTitle("")
        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._message = QLabel()
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setWordWrap(True)

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
        self._chart.removeAllSeries()
        for axis in self._chart.axes():
            self._chart.removeAxis(axis)

        series = QLineSeries()
        series.append(
            [QPointF(time_s * 1e9, value) for time_s, value in zip(trace.time_s, trace.values)]
        )
        self._chart.addSeries(series)

        x_axis = QValueAxis()
        x_axis.setTitleText(self._localization.text("results.plot.time_ns"))
        x_axis.setLabelFormat("%.3g")
        y_axis = QValueAxis()
        y_axis.setTitleText(trace.metadata.component)
        y_axis.setLabelFormat("%.3g")

        self._chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(x_axis)
        series.attachAxis(y_axis)
        self._chart.setTitle(
            self._localization.text(
                "results.plot.ascan_chart_title",
                receiver_name=trace.metadata.receiver_name,
                component=trace.metadata.component,
            )
        )
        self._layout.setCurrentWidget(self._chart_view)

    def retranslate_ui(self) -> None:
        self._chart.setTitle(self._localization.text("results.plot.ascan_title"))
        self._message.setText(self._localization.text("results.plot.ascan_prompt"))
