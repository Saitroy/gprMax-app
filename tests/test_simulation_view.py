from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.domain.execution_status import SimulationMode
from gprmax_workbench.domain.gprmax_config import SimulationRunConfig
from gprmax_workbench.ui.views.simulation_view import (
    SimulationConfigurationError,
    SimulationView,
)


class SimulationViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_hides_gpu_controls_and_returns_cpu_only_configuration(self) -> None:
        view = SimulationView(
            localization=LocalizationService("en"),
            runtime_label="Bundled runtime",
        )

        self.assertIsNone(view.findChild(QWidget, "simulation.gpu_checkbox"))
        self.assertIsNone(view.findChild(QWidget, "simulation.gpu_devices"))

        configuration = view.current_configuration()

        self.assertFalse(configuration.use_gpu)
        self.assertEqual(configuration.gpu_device_ids, [])

    def test_set_configuration_updates_form_controls(self) -> None:
        view = SimulationView(
            localization=LocalizationService("en"),
            runtime_label="Bundled runtime",
        )

        view.set_configuration(
            SimulationRunConfig(
                mode=SimulationMode.GEOMETRY_ONLY,
                benchmark=True,
                geometry_fixed=True,
                write_processed=True,
                num_model_runs=60,
                restart_from_model=5,
                mpi_tasks=4,
                mpi_no_spawn=True,
                extra_arguments=["--foo", "bar"],
            )
        )

        configuration = view.current_configuration()

        self.assertEqual(configuration.mode, SimulationMode.GEOMETRY_ONLY)
        self.assertEqual(configuration.num_model_runs, 60)
        self.assertEqual(configuration.restart_from_model, 5)
        self.assertEqual(configuration.mpi_tasks, 4)
        self.assertTrue(configuration.benchmark)
        self.assertTrue(configuration.geometry_fixed)
        self.assertTrue(configuration.write_processed)
        self.assertTrue(configuration.mpi_no_spawn)
        self.assertEqual(configuration.extra_arguments, ["--foo", "bar"])

    def test_invalid_extra_args_raise_configuration_error(self) -> None:
        view = SimulationView(
            localization=LocalizationService("en"),
            runtime_label="Bundled runtime",
        )
        view._extra_args_edit.setText('\"broken')

        with self.assertRaises(SimulationConfigurationError):
            view.current_configuration()

    def test_standard_desktop_width_keeps_splitters_horizontal(self) -> None:
        view = SimulationView(
            localization=LocalizationService("en"),
            runtime_label="Bundled runtime",
        )

        view.resize(1040, 720)
        view.show()
        self._app.processEvents()

        self.assertEqual(view._content_splitter.orientation(), Qt.Orientation.Horizontal)  # noqa: SLF001
        self.assertEqual(view._top_splitter.orientation(), Qt.Orientation.Horizontal)  # noqa: SLF001
        self.assertGreaterEqual(view._content_splitter.handleWidth(), 10)  # noqa: SLF001
        self.assertGreaterEqual(view._top_splitter.handleWidth(), 10)  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
