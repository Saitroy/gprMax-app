from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.domain.traces import BscanDataset, BscanLoadResult
from gprmax_workbench.ui.widgets.results.bscan_image_widget import BscanImageWidget


class BscanImageWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_set_result_accepts_non_contiguous_image_source(self) -> None:
        widget = BscanImageWidget(LocalizationService("en"))
        widget.resize(640, 320)
        widget.show()

        result = BscanLoadResult(
            available=True,
            message="ok",
            dataset=BscanDataset(
                receiver_id="rx1",
                receiver_name="Rx 1",
                component="Ex",
                time_s=[0.0, 1.0, 2.0],
                amplitudes=[
                    [0.0, 1.0, 0.0],
                    [1.0, 0.0, -1.0],
                    [0.0, -1.0, 0.0],
                ],
            ),
        )

        widget.set_result(result)

        self.assertIsNotNone(widget._image.pixmap())
        self.assertFalse(widget._image.pixmap().isNull())

    def test_resize_rescales_from_source_pixmap(self) -> None:
        widget = BscanImageWidget(LocalizationService("en"))
        widget.resize(640, 320)
        widget.show()

        result = BscanLoadResult(
            available=True,
            message="ok",
            dataset=BscanDataset(
                receiver_id="rx1",
                receiver_name="Rx 1",
                component="Ex",
                time_s=[0.0, 1.0, 2.0],
                amplitudes=[
                    [0.0, 1.0, 0.0],
                    [1.0, 0.0, -1.0],
                    [0.0, -1.0, 0.0],
                ],
            ),
        )

        widget.set_result(result)
        first_size = widget._image.pixmap().size()

        widget.resize(480, 480)
        widget.repaint()

        self.assertFalse(widget._source_pixmap.isNull())
        self.assertNotEqual(first_size, widget._image.pixmap().size())


if __name__ == "__main__":
    unittest.main()
