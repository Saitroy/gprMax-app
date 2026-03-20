from __future__ import annotations

from math import ceil, floor, log10

import numpy as np
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ....application.services.localization_service import LocalizationService
from ....domain.traces import BscanDataset, BscanLoadResult


def _nice_step(value: float) -> float:
    if value <= 0:
        return 1.0
    exponent = floor(log10(value))
    fraction = value / (10 ** exponent)
    if fraction < 1.5:
        nice_fraction = 1.0
    elif fraction < 3.0:
        nice_fraction = 2.0
    elif fraction < 7.0:
        nice_fraction = 5.0
    else:
        nice_fraction = 10.0
    return nice_fraction * (10 ** exponent)


class _BscanCanvas(QWidget):
    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._source_pixmap = QPixmap()
        self._display_pixmap = QPixmap()
        self._dataset: BscanDataset | None = None
        self.setMinimumHeight(340)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_payload(self, dataset: BscanDataset, pixmap: QPixmap) -> None:
        self._dataset = dataset
        self._source_pixmap = pixmap
        self._refresh_display_pixmap()
        self.update()

    def clear(self) -> None:
        self._dataset = None
        self._source_pixmap = QPixmap()
        self._display_pixmap = QPixmap()
        self.update()

    def pixmap(self) -> QPixmap:
        return self._display_pixmap

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_display_pixmap()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), QColor("#fbfbfa"))

        plot_rect = self._plot_rect()
        painter.fillRect(plot_rect, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#cbd5e1"), 1.0))
        painter.drawRect(plot_rect)

        if self._source_pixmap.isNull() or self._dataset is None:
            self._display_pixmap = QPixmap()
            return

        self._refresh_display_pixmap()
        painter.drawPixmap(plot_rect.toRect(), self._display_pixmap)
        self._draw_grid(painter, plot_rect)
        self._draw_axes(painter, plot_rect)

    def _plot_rect(self) -> QRectF:
        outer = self.rect().adjusted(0, 0, -1, -1)
        left_margin = max(64, int(outer.width() * 0.12))
        right_margin = max(20, int(outer.width() * 0.04))
        top_margin = max(20, int(outer.height() * 0.06))
        bottom_margin = max(44, int(outer.height() * 0.12))
        width = max(outer.width() - left_margin - right_margin, 20)
        height = max(outer.height() - top_margin - bottom_margin, 20)
        return QRectF(left_margin, top_margin, width, height)

    def _refresh_display_pixmap(self) -> None:
        if self._source_pixmap.isNull():
            self._display_pixmap = QPixmap()
            return
        plot_rect = self._plot_rect()
        self._display_pixmap = self._source_pixmap.scaled(
            plot_rect.size().toSize(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _draw_grid(self, painter: QPainter, plot_rect: QRectF) -> None:
        dataset = self._dataset
        if dataset is None:
            return

        painter.save()
        painter.setPen(QPen(QColor(255, 255, 255, 110), 1.0, Qt.PenStyle.DashLine))
        for index in self._trace_tick_indexes():
            x = self._trace_index_to_x(index, plot_rect)
            painter.drawLine(x, plot_rect.top(), x, plot_rect.bottom())
        for value_ns in self._time_ticks_ns():
            y = self._time_to_y(value_ns, plot_rect)
            painter.drawLine(plot_rect.left(), y, plot_rect.right(), y)
        painter.restore()

    def _draw_axes(self, painter: QPainter, plot_rect: QRectF) -> None:
        dataset = self._dataset
        if dataset is None:
            return

        painter.save()
        axis_pen = QPen(QColor("#506273"), 1.0)
        painter.setPen(axis_pen)
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.topLeft(), plot_rect.bottomLeft())

        for index in self._trace_tick_indexes():
            x = self._trace_index_to_x(index, plot_rect)
            painter.drawLine(x, plot_rect.bottom(), x, plot_rect.bottom() + 6)
            painter.drawText(
                QRectF(x - 28, plot_rect.bottom() + 8, 56, 16),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                str(index + 1),
            )

        for value_ns in self._time_ticks_ns():
            y = self._time_to_y(value_ns, plot_rect)
            painter.drawLine(plot_rect.left() - 6, y, plot_rect.left(), y)
            painter.drawText(
                QRectF(4, y - 8, plot_rect.left() - 12, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{value_ns:.3g}",
            )

        painter.drawText(
            QRectF(plot_rect.left(), plot_rect.bottom() + 24, plot_rect.width(), 18),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            self._localization.text("results.plot.trace_number"),
        )

        painter.save()
        painter.translate(18, plot_rect.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot_rect.height() / 2, -10, plot_rect.height(), 20),
            Qt.AlignmentFlag.AlignCenter,
            self._localization.text("results.plot.time_ns"),
        )
        painter.restore()

        painter.drawText(
            QRectF(plot_rect.left(), 2, plot_rect.width(), 18),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            dataset.component,
        )
        painter.restore()

    def _trace_tick_indexes(self) -> list[int]:
        dataset = self._dataset
        if dataset is None or dataset.trace_count <= 0:
            return []
        if dataset.trace_count == 1:
            return [0]
        target_ticks = max(2, int(self.width() / 110))
        step = max(1, ceil(dataset.trace_count / target_ticks))
        ticks = list(range(0, dataset.trace_count, step))
        if ticks[-1] != dataset.trace_count - 1:
            ticks.append(dataset.trace_count - 1)
        return ticks

    def _time_ticks_ns(self) -> list[float]:
        dataset = self._dataset
        if dataset is None or not dataset.time_s:
            return []
        maximum_ns = dataset.time_s[-1] * 1e9
        if maximum_ns <= 0:
            return [0.0]
        target_ticks = max(2, int(self.height() / 80))
        step = _nice_step(maximum_ns / target_ticks)
        value = 0.0
        ticks: list[float] = []
        while value <= maximum_ns + step * 0.25:
            ticks.append(value)
            value += step
        if abs(ticks[-1] - maximum_ns) > step * 0.2:
            ticks.append(maximum_ns)
        return ticks

    def _trace_index_to_x(self, index: int, plot_rect: QRectF) -> float:
        dataset = self._dataset
        if dataset is None or dataset.trace_count <= 1:
            return plot_rect.center().x()
        ratio = index / (dataset.trace_count - 1)
        return plot_rect.left() + ratio * plot_rect.width()

    def _time_to_y(self, value_ns: float, plot_rect: QRectF) -> float:
        dataset = self._dataset
        if dataset is None or not dataset.time_s:
            return plot_rect.top()
        maximum_ns = dataset.time_s[-1] * 1e9
        if maximum_ns <= 0:
            return plot_rect.top()
        ratio = value_ns / maximum_ns
        return plot_rect.top() + ratio * plot_rect.height()


class BscanImageWidget(QWidget):
    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._source_pixmap = QPixmap()
        self._message = QLabel()
        self._message.setWordWrap(True)
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image = _BscanCanvas(localization)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._image, 1)
        layout.addWidget(self._message)
        self.retranslate_ui()

    def set_result(self, result: BscanLoadResult) -> None:
        self._message.setText(self._localization.translate_message(result.message))
        if not result.available or result.dataset is None:
            self._source_pixmap = QPixmap()
            self._image.clear()
            return

        array = np.asarray(result.dataset.amplitudes, dtype=float)
        if array.size == 0:
            self._source_pixmap = QPixmap()
            self._image.clear()
            self._message.setText(self._localization.text("results.plot.bscan_empty"))
            return

        image_array = self._to_image_array(array)
        height, width, _channels = image_array.shape
        qimage = QImage(
            image_array.data,
            width,
            height,
            image_array.strides[0],
            QImage.Format.Format_RGB888,
        ).copy()
        self._source_pixmap = QPixmap.fromImage(qimage)
        self._image.set_payload(result.dataset, self._source_pixmap)

    def retranslate_ui(self) -> None:
        if self._source_pixmap.isNull():
            self._message.setText(self._localization.text("results.plot.bscan_placeholder"))

    def _to_image_array(self, amplitudes: np.ndarray) -> np.ndarray:
        matrix = amplitudes.T
        max_abs = float(np.max(np.abs(matrix))) if matrix.size else 0.0
        if max_abs <= 0:
            normalized = np.full_like(matrix, 0.5, dtype=float)
        else:
            normalized = np.clip((matrix / max_abs + 1.0) / 2.0, 0.0, 1.0)

        red = (normalized * 255).astype(np.uint8)
        green = (255 - np.abs(normalized - 0.5) * 2 * 255).clip(0, 255).astype(np.uint8)
        blue = ((1.0 - normalized) * 255).astype(np.uint8)
        return np.ascontiguousarray(np.dstack((red, green, blue)))
