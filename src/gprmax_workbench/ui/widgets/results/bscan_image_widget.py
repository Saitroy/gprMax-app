from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ....application.services.localization_service import LocalizationService
from ....domain.traces import BscanLoadResult


class BscanImageWidget(QWidget):
    def __init__(
        self,
        localization: LocalizationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._message = QLabel()
        self._message.setWordWrap(True)
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image = QLabel()
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setMinimumHeight(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._image, 1)
        layout.addWidget(self._message)
        self.retranslate_ui()

    def set_result(self, result: BscanLoadResult) -> None:
        self._message.setText(self._localization.translate_message(result.message))
        if not result.available or result.dataset is None:
            self._image.clear()
            return

        array = np.asarray(result.dataset.amplitudes, dtype=float)
        if array.size == 0:
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
        pixmap = QPixmap.fromImage(qimage).scaled(
            self._image.size() if self._image.size().isValid() else self._image.minimumSizeHint(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image.setPixmap(pixmap)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        pixmap = self._image.pixmap()
        if pixmap is None or pixmap.isNull():
            return
        self._image.setPixmap(
            pixmap.scaled(
                self._image.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def retranslate_ui(self) -> None:
        pixmap = self._image.pixmap()
        if pixmap is None or pixmap.isNull():
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
        return np.dstack((red, green, blue))
