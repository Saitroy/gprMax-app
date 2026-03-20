from __future__ import annotations

import copy
from dataclasses import dataclass
from math import ceil, floor, log10

from PySide6.QtCore import QMimeData, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDrag, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.models import GeometryPrimitive, Project, Vector3
from ...layouts.flow_layout import FlowLayout
from .helpers import build_float_spinbox, build_status_label, join_messages


@dataclass(slots=True)
class _SceneEntityRef:
    kind: str
    index: int
    label: str


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


class _PaletteButton(QPushButton):
    def __init__(self, entity_kind: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entity_kind = entity_kind

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return super().mouseMoveEvent(event)
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.entity_kind)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class _CanvasView(QGraphicsView):
    entity_dropped = Signal(str, float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        self.setMinimumHeight(420)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        if event.mimeData().hasText():
            point = self.mapToScene(event.position().toPoint())
            self.entity_dropped.emit(event.mimeData().text(), point.x(), point.y())
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        scene = self.scene()
        if scene is not None and not scene.sceneRect().isNull():
            self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class _MetricRuler(QWidget):
    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._orientation = orientation
        self._minimum = 0.0
        self._maximum = 1.0
        self._axis_name = "X"
        self._unit = "m"
        if orientation == Qt.Orientation.Horizontal:
            self.setMinimumHeight(34)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setMinimumWidth(64)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def set_scale(self, minimum: float, maximum: float, axis_name: str, unit: str = "m") -> None:
        self._minimum = float(minimum)
        self._maximum = float(maximum)
        self._axis_name = axis_name
        self._unit = unit
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.fillRect(self.rect(), QColor("#edf3f7"))
        painter.setPen(QPen(QColor("#c7d2db"), 1.0))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        if self._maximum <= self._minimum:
            return

        label = f"{self._axis_name}, {self._unit}"
        if self._orientation == Qt.Orientation.Horizontal:
            left = 10
            right = self.width() - 10
            baseline = self.height() - 10
            painter.setPen(QColor("#506273"))
            painter.drawLine(left, baseline, right, baseline)
            painter.drawText(left, 14, label)
            available = max(right - left, 1)
            target_ticks = max(2, int(available / 90))
            step = _nice_step((self._maximum - self._minimum) / target_ticks)
            value = ceil(self._minimum / step) * step
            painter.setPen(QColor("#6f8293"))
            while value <= self._maximum + step * 0.25:
                ratio = (value - self._minimum) / (self._maximum - self._minimum)
                x = left + ratio * available
                painter.drawLine(QPointF(x, baseline), QPointF(x, baseline - 6))
                painter.drawText(
                    QRectF(x - 28, baseline - 22, 56, 16),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                    f"{value:.3g}",
                )
                value += step
            return

        top = 10
        bottom = self.height() - 10
        baseline = self.width() - 10
        painter.setPen(QColor("#506273"))
        painter.drawLine(baseline, top, baseline, bottom)
        painter.drawText(8, 14, label)
        available = max(bottom - top, 1)
        target_ticks = max(2, int(available / 72))
        step = _nice_step((self._maximum - self._minimum) / target_ticks)
        value = ceil(self._minimum / step) * step
        painter.setPen(QColor("#6f8293"))
        while value <= self._maximum + step * 0.25:
            ratio = (value - self._minimum) / (self._maximum - self._minimum)
            y = top + ratio * available
            painter.drawLine(QPointF(baseline, y), QPointF(baseline - 6, y))
            painter.drawText(
                QRectF(2, y - 8, baseline - 10, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{value:.3g}",
            )
            value += step


class _AnchorItem(QGraphicsObject):
    def __init__(self, entity_ref: _SceneEntityRef, color: QColor, shape: str, on_release) -> None:
        super().__init__()
        self.entity_ref = entity_ref
        self._color = color
        self._shape = shape
        self._on_release = on_release
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
        )
        self.setZValue(20)

    def boundingRect(self) -> QRectF:
        return QRectF(-8.0, -8.0, 16.0, 16.0)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(QPen(self._color.darker(120), 1.5))
        painter.setBrush(QBrush(self._color))
        if self._shape == "diamond":
            path = QPainterPath()
            path.moveTo(0, -7)
            path.lineTo(7, 0)
            path.lineTo(0, 7)
            path.lineTo(-7, 0)
            path.closeSubpath()
            painter.drawPath(path)
            return
        if self._shape == "triangle":
            path = QPainterPath()
            path.moveTo(0, -7)
            path.lineTo(7, 6)
            path.lineTo(-7, 6)
            path.closeSubpath()
            painter.drawPath(path)
            return
        painter.drawEllipse(self.boundingRect())

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self._on_release(self.entity_ref, self.scenePos())


class SceneCanvasPanel(QWidget):
    model_changed = Signal()

    def __init__(
        self,
        localization: LocalizationService,
        model_editor_service: ModelEditorService,
        validation_service: ValidationService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._model_editor_service = model_editor_service
        self._validation_service = validation_service
        self._project: Project | None = None
        self._plane = "xy"
        self._selected_entity_ref: _SceneEntityRef | None = None

        self._plane_combo = QComboBox()
        self._plane_combo.currentIndexChanged.connect(self._change_plane)
        self._snap_to_grid = QCheckBox()
        self._snap_to_grid.toggled.connect(self._refresh_scene)
        self._grid_step = build_float_spinbox(minimum=0.001, maximum=10.0, decimals=4, step=0.001)
        self._grid_step.setValue(0.01)
        self._grid_step.valueChanged.connect(self._refresh_scene)

        self._entity_list = QListWidget()
        self._entity_list.currentRowChanged.connect(self._select_entity_from_list)
        self._status_label = build_status_label("")
        self._hint_label = QLabel()
        self._hint_label.setWordWrap(True)

        self._scene = QGraphicsScene(self)
        self._view = _CanvasView()
        self._view.setScene(self._scene)
        self._view.entity_dropped.connect(self._on_entity_dropped)
        self._horizontal_ruler = _MetricRuler(Qt.Orientation.Horizontal)
        self._vertical_ruler = _MetricRuler(Qt.Orientation.Vertical)

        self._palette_buttons: list[_PaletteButton] = []
        palette = QWidget()
        palette_layout = QVBoxLayout(palette)
        palette_layout.setContentsMargins(0, 0, 0, 0)
        self._palette_title = QLabel()
        palette_layout.addWidget(self._palette_title)
        buttons_layout = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        for entity_kind in ("box", "sphere", "cylinder", "source", "receiver", "antenna", "import"):
            button = _PaletteButton(entity_kind)
            button.clicked.connect(lambda checked=False, kind=entity_kind: self._add_entity_at_center(kind))
            self._palette_buttons.append(button)
            buttons_layout.addWidget(button)
        palette_layout.addLayout(buttons_layout)

        self._selected_label = QLabel()
        self._selected_label.setWordWrap(True)
        self._pos_x = build_float_spinbox()
        self._pos_y = build_float_spinbox()
        self._pos_z = build_float_spinbox()
        self._nudge_step = build_float_spinbox(minimum=0.001, maximum=10.0, decimals=4, step=0.001)
        self._nudge_step.setValue(0.01)
        self._apply_button = QPushButton()
        self._apply_button.clicked.connect(self._apply_entity_changes)
        self._duplicate_button = QPushButton()
        self._duplicate_button.clicked.connect(self._duplicate_selected)
        self._delete_button = QPushButton()
        self._delete_button.clicked.connect(self._delete_selected)
        self._pos_x_label = QLabel()
        self._pos_y_label = QLabel()
        self._pos_z_label = QLabel()
        self._nudge_step_label = QLabel()

        inspector = QFrame()
        inspector.setObjectName("ViewCard")
        inspector_layout = QVBoxLayout(inspector)
        inspector_layout.setContentsMargins(12, 12, 12, 12)
        inspector_layout.setSpacing(10)
        self._inspector_title = QLabel()
        inspector_layout.addWidget(self._inspector_title)
        inspector_layout.addWidget(self._selected_label)
        inspector_form = QFormLayout()
        inspector_form.addRow(self._pos_x_label, self._pos_x)
        inspector_form.addRow(self._pos_y_label, self._pos_y)
        inspector_form.addRow(self._pos_z_label, self._pos_z)
        inspector_form.addRow(self._nudge_step_label, self._nudge_step)
        inspector_layout.addLayout(inspector_form)
        self._nudge_layout = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        inspector_layout.addLayout(self._nudge_layout)
        self._action_layout = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        self._action_layout.addWidget(self._apply_button)
        self._action_layout.addWidget(self._duplicate_button)
        self._action_layout.addWidget(self._delete_button)
        inspector_layout.addLayout(self._action_layout)

        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        plane_row = QHBoxLayout()
        self._plane_label = QLabel()
        plane_row.addWidget(self._plane_label)
        plane_row.addWidget(self._plane_combo)
        side_layout.addLayout(plane_row)
        snap_form = QFormLayout()
        self._grid_step_label_global = QLabel()
        snap_form.addRow("", self._snap_to_grid)
        snap_form.addRow(self._grid_step_label_global, self._grid_step)
        side_layout.addLayout(snap_form)
        side_layout.addWidget(self._hint_label)
        side_layout.addWidget(palette)
        self._entities_title = QLabel()
        side_layout.addWidget(self._entities_title)
        side_layout.addWidget(self._entity_list, 1)
        side_layout.addWidget(inspector)
        side_layout.addWidget(self._status_label)

        view_shell = QWidget()
        view_shell_layout = QGridLayout(view_shell)
        view_shell_layout.setContentsMargins(0, 0, 0, 0)
        view_shell_layout.setSpacing(0)
        corner = QLabel()
        corner.setMinimumSize(64, 34)
        corner.setStyleSheet("background:#edf3f7; border: 1px solid #c7d2db;")
        view_shell_layout.addWidget(corner, 0, 0)
        view_shell_layout.addWidget(self._horizontal_ruler, 0, 1)
        view_shell_layout.addWidget(self._vertical_ruler, 1, 0)
        view_shell_layout.addWidget(self._view, 1, 1)
        view_shell_layout.setColumnStretch(1, 1)
        view_shell_layout.setRowStretch(1, 1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(side_panel, 0)
        layout.addWidget(view_shell, 1)

        self._build_nudge_buttons()
        self.retranslate_ui()
        self.set_project(None)

    def _build_nudge_buttons(self) -> None:
        self._nudge_buttons: list[QPushButton] = []
        for text_key, vector in (
            ("editor.scene.nudge.left", (-1, 0, 0)),
            ("editor.scene.nudge.right", (1, 0, 0)),
            ("editor.scene.nudge.down", (0, -1, 0)),
            ("editor.scene.nudge.up", (0, 1, 0)),
            ("editor.scene.nudge.back", (0, 0, -1)),
            ("editor.scene.nudge.forward", (0, 0, 1)),
        ):
            button = QPushButton()
            button.clicked.connect(
                lambda checked=False, delta=vector: self._nudge_selected(*delta)
            )
            button.setProperty("text_key", text_key)
            self._nudge_layout.addWidget(button)
            self._nudge_buttons.append(button)

    def retranslate_ui(self) -> None:
        self._plane_label.setText(self._localization.text("editor.scene.plane"))
        self._palette_title.setText(self._localization.text("editor.scene.palette"))
        self._entities_title.setText(self._localization.text("editor.scene.entities"))
        self._hint_label.setText(self._localization.text("editor.scene.hint"))
        self._snap_to_grid.setText(self._localization.text("editor.scene.snap"))
        self._grid_step_label_global.setText(self._localization.text("editor.scene.grid_step"))
        self._inspector_title.setText(self._localization.text("editor.scene.inspector"))
        self._apply_button.setText(self._localization.text("editor.scene.apply"))
        self._duplicate_button.setText(self._localization.text("common.duplicate"))
        self._delete_button.setText(self._localization.text("common.delete"))
        self._pos_x_label.setText(self._localization.text("editor.scene.position_x"))
        self._pos_y_label.setText(self._localization.text("editor.scene.position_y"))
        self._pos_z_label.setText(self._localization.text("editor.scene.position_z"))
        self._nudge_step_label.setText(self._localization.text("editor.scene.nudge_step"))
        for button in self._nudge_buttons:
            button.setText(self._localization.text(str(button.property("text_key"))))
        self._plane_combo.blockSignals(True)
        current_plane = self._plane_combo.currentData()
        self._plane_combo.clear()
        for plane_key, plane_label in (("xy", "XY"), ("xz", "XZ"), ("yz", "YZ")):
            self._plane_combo.addItem(plane_label, plane_key)
        index = self._plane_combo.findData(current_plane or self._plane)
        self._plane_combo.setCurrentIndex(index if index >= 0 else 0)
        self._plane_combo.blockSignals(False)
        for button in self._palette_buttons:
            button.setText(self._localization.text(f"editor.scene.entity.{button.entity_kind}"))
        self.refresh_validation()

    def set_project(self, project: Project | None) -> None:
        self._project = project
        self._refresh_scene()
        self.refresh_validation()

    def refresh_validation(self) -> None:
        prefixes = [
            "model.geometry",
            "model.sources",
            "model.receivers",
            "model.geometry_imports",
            "model.antenna_models",
        ]
        self._status_label.setText(
            join_messages(
                self._validation_service.messages_for_prefixes(*prefixes),
                self._localization.text("editor.scene.valid"),
            )
        )

    def _change_plane(self) -> None:
        self._plane = str(self._plane_combo.currentData() or "xy")
        self._refresh_scene()

    def _refresh_scene(self) -> None:
        selection = self._selection_signature()
        self._scene.clear()
        self._entity_list.clear()
        self._selected_entity_ref = None
        if self._project is None:
            self._scene.setSceneRect(QRectF(0, 0, 1, 1))
            self._update_rulers(1.0, 1.0)
            self._load_entity_details(None)
            return

        width, height = self._plane_limits(self._project)
        self._update_rulers(width, height)
        self._scene.setSceneRect(QRectF(0, 0, width, height))
        background = QGraphicsRectItem(QRectF(0, 0, width, height))
        background.setBrush(QBrush(QColor("#f8fafc")))
        background.setPen(QPen(QColor("#cbd5e1"), 1.2))
        background.setZValue(-10)
        self._scene.addItem(background)
        self._draw_grid(width, height)

        for index, geometry in enumerate(self._project.model.geometry):
            self._draw_geometry(geometry)
            self._add_anchor(
                _SceneEntityRef("geometry", index, geometry.label or geometry.kind),
                self._geometry_anchor_position(geometry),
                QColor("#2563eb"),
                "diamond",
            )
        for index, source in enumerate(self._project.model.sources):
            self._add_anchor(
                _SceneEntityRef("source", index, source.identifier or f"source_{index + 1}"),
                self._project_point(source.position_m),
                QColor("#dc2626"),
                "triangle",
            )
        for index, receiver in enumerate(self._project.model.receivers):
            self._add_anchor(
                _SceneEntityRef("receiver", index, receiver.identifier or f"receiver_{index + 1}"),
                self._project_point(receiver.position_m),
                QColor("#16a34a"),
                "ellipse",
            )
        for index, antenna in enumerate(self._project.model.antenna_models):
            self._add_anchor(
                _SceneEntityRef("antenna", index, antenna.identifier or f"antenna_{index + 1}"),
                self._project_point(antenna.position_m),
                QColor("#7c3aed"),
                "diamond",
            )
        for index, geometry_import in enumerate(self._project.model.geometry_imports):
            self._add_anchor(
                _SceneEntityRef("import", index, geometry_import.identifier or f"import_{index + 1}"),
                self._project_point(geometry_import.position_m),
                QColor("#0f766e"),
                "ellipse",
            )
        self._restore_selection(selection)
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _draw_grid(self, width: float, height: float) -> None:
        step = self._grid_step.value() if self._snap_to_grid.isChecked() else self._grid_spacing_for_scene(width, height)
        grid_pen = QPen(QColor("#d8e2ea"), 0)
        x = step
        while x < width:
            self._scene.addLine(x, 0, x, height, grid_pen)
            x += step
        y = step
        while y < height:
            self._scene.addLine(0, y, width, y, grid_pen)
            y += step

    def _draw_geometry(self, geometry: GeometryPrimitive) -> None:
        overlay_pen = QPen(QColor("#93c5fd"), 1.2)
        overlay_brush = QBrush(QColor(59, 130, 246, 50))
        if geometry.kind == "box":
            lower = self._parameters_point(geometry.parameters.get("lower_left_m", {}))
            upper = self._parameters_point(geometry.parameters.get("upper_right_m", {}))
            rect = QRectF(
                min(lower.x(), upper.x()),
                min(lower.y(), upper.y()),
                abs(upper.x() - lower.x()),
                abs(upper.y() - lower.y()),
            )
            self._scene.addRect(rect, overlay_pen, overlay_brush)
            return
        if geometry.kind == "sphere":
            center = self._parameters_point(geometry.parameters.get("center_m", {}))
            radius = float(geometry.parameters.get("radius_m", 0.0))
            self._scene.addEllipse(
                QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                overlay_pen,
                overlay_brush,
            )
            return
        if geometry.kind == "cylinder":
            start = self._parameters_point(geometry.parameters.get("start_m", {}))
            end = self._parameters_point(geometry.parameters.get("end_m", {}))
            self._scene.addLine(start.x(), start.y(), end.x(), end.y(), overlay_pen)

    def _add_anchor(self, entity_ref: _SceneEntityRef, position: QPointF, color: QColor, shape: str) -> None:
        item = _AnchorItem(entity_ref, color, shape, self._move_entity_from_anchor)
        item.setPos(position)
        self._scene.addItem(item)
        list_item = QListWidgetItem(f"{entity_ref.kind}: {entity_ref.label}")
        list_item.setData(Qt.ItemDataRole.UserRole, entity_ref)
        self._entity_list.addItem(list_item)

    def _select_entity_from_list(self, row: int) -> None:
        if row < 0:
            self._selected_entity_ref = None
            self._load_entity_details(None)
            return
        entity_ref = self._entity_list.item(row).data(Qt.ItemDataRole.UserRole)
        self._selected_entity_ref = entity_ref
        for item in self._scene.items():
            if isinstance(item, _AnchorItem):
                item.setSelected(
                    item.entity_ref.kind == entity_ref.kind
                    and item.entity_ref.index == entity_ref.index
                )
        self._load_entity_details(entity_ref)

    def _load_entity_details(self, entity_ref: _SceneEntityRef | None) -> None:
        self._selected_entity_ref = entity_ref
        enabled = entity_ref is not None
        for widget in (
            self._pos_x,
            self._pos_y,
            self._pos_z,
            self._nudge_step,
            self._apply_button,
            self._duplicate_button,
            self._delete_button,
            *self._nudge_buttons,
        ):
            widget.setEnabled(enabled)
        if entity_ref is None or self._project is None:
            self._selected_label.setText(self._localization.text("editor.scene.none_selected"))
            for spinbox in (self._pos_x, self._pos_y, self._pos_z):
                spinbox.setValue(0.0)
            return
        entity = self._entity_for_ref(entity_ref)
        position = self._entity_position(entity_ref, entity)
        self._selected_label.setText(f"{entity_ref.kind}: {entity_ref.label}")
        self._pos_x.setValue(position.x)
        self._pos_y.setValue(position.y)
        self._pos_z.setValue(position.z)

    def _on_entity_dropped(self, entity_kind: str, scene_x: float, scene_y: float) -> None:
        if self._project is None:
            return
        self._add_entity(entity_kind, QPointF(scene_x, scene_y))

    def _add_entity_at_center(self, entity_kind: str) -> None:
        if self._project is None:
            return
        self._add_entity(entity_kind, self._scene.sceneRect().center())

    def _add_entity(self, entity_kind: str, point: QPointF) -> None:
        project = self._model_editor_service.require_current_project()
        vector = self._vector_from_scene_point(point)
        if entity_kind in {"box", "sphere", "cylinder"}:
            index = self._model_editor_service.add_geometry(kind=entity_kind)
            geometry = copy.deepcopy(project.model.geometry[index])
            self._model_editor_service.update_geometry(index, self._move_geometry_to_anchor(geometry, vector))
            self._refresh_scene()
            self._set_selected_row("geometry", index)
        elif entity_kind == "source":
            index = self._model_editor_service.add_source()
            source = copy.deepcopy(project.model.sources[index])
            source.position_m = vector
            self._model_editor_service.update_source(index, source)
            self._refresh_scene()
            self._set_selected_row("source", index)
        elif entity_kind == "receiver":
            index = self._model_editor_service.add_receiver()
            receiver = copy.deepcopy(project.model.receivers[index])
            receiver.position_m = vector
            self._model_editor_service.update_receiver(index, receiver)
            self._refresh_scene()
            self._set_selected_row("receiver", index)
        elif entity_kind == "antenna":
            index = self._model_editor_service.add_antenna_model()
            antenna = copy.deepcopy(project.model.antenna_models[index])
            antenna.position_m = vector
            self._model_editor_service.update_antenna_model(index, antenna)
            self._refresh_scene()
            self._set_selected_row("antenna", index)
        elif entity_kind == "import":
            index = self._model_editor_service.add_geometry_import()
            geometry_import = copy.deepcopy(project.model.geometry_imports[index])
            geometry_import.position_m = vector
            self._model_editor_service.update_geometry_import(index, geometry_import)
            self._refresh_scene()
            self._set_selected_row("import", index)
        self.refresh_validation()
        self.model_changed.emit()

    def _move_entity_from_anchor(self, entity_ref: _SceneEntityRef, point: QPointF) -> None:
        if self._project is None:
            return
        vector = self._vector_from_scene_point(point)
        self._apply_entity_position(entity_ref, vector)
        self._refresh_scene()
        self._set_selected_row(entity_ref.kind, entity_ref.index)
        self.refresh_validation()
        self.model_changed.emit()

    def _apply_entity_changes(self) -> None:
        if self._selected_entity_ref is None:
            return
        self._apply_entity_position(
            self._selected_entity_ref,
            Vector3(self._pos_x.value(), self._pos_y.value(), self._pos_z.value()),
        )
        self._refresh_scene()
        self._set_selected_row(self._selected_entity_ref.kind, self._selected_entity_ref.index)
        self.refresh_validation()
        self.model_changed.emit()

    def _duplicate_selected(self) -> None:
        if self._selected_entity_ref is None:
            return
        entity_ref = self._selected_entity_ref
        if entity_ref.kind == "geometry":
            new_index = self._model_editor_service.duplicate_geometry(entity_ref.index)
        elif entity_ref.kind == "source":
            new_index = self._model_editor_service.duplicate_source(entity_ref.index)
        elif entity_ref.kind == "receiver":
            new_index = self._model_editor_service.duplicate_receiver(entity_ref.index)
        elif entity_ref.kind == "antenna":
            new_index = self._model_editor_service.duplicate_antenna_model(entity_ref.index)
        else:
            new_index = self._model_editor_service.duplicate_geometry_import(entity_ref.index)
        self._refresh_scene()
        self._set_selected_row(entity_ref.kind, new_index)
        self.refresh_validation()
        self.model_changed.emit()

    def _delete_selected(self) -> None:
        if self._selected_entity_ref is None:
            return
        entity_ref = self._selected_entity_ref
        if entity_ref.kind == "geometry":
            next_index = self._model_editor_service.delete_geometry(entity_ref.index)
        elif entity_ref.kind == "source":
            next_index = self._model_editor_service.delete_source(entity_ref.index)
        elif entity_ref.kind == "receiver":
            next_index = self._model_editor_service.delete_receiver(entity_ref.index)
        elif entity_ref.kind == "antenna":
            next_index = self._model_editor_service.delete_antenna_model(entity_ref.index)
        else:
            next_index = self._model_editor_service.delete_geometry_import(entity_ref.index)
        self._refresh_scene()
        if next_index is not None:
            self._set_selected_row(entity_ref.kind, next_index)
        self.refresh_validation()
        self.model_changed.emit()

    def _nudge_selected(self, dx: int, dy: int, dz: int) -> None:
        if self._selected_entity_ref is None:
            return
        step = self._nudge_step.value()
        self._apply_entity_position(
            self._selected_entity_ref,
            Vector3(
                self._pos_x.value() + dx * step,
                self._pos_y.value() + dy * step,
                self._pos_z.value() + dz * step,
            ),
        )
        self._refresh_scene()
        self._set_selected_row(self._selected_entity_ref.kind, self._selected_entity_ref.index)
        self.refresh_validation()
        self.model_changed.emit()

    def _apply_entity_position(self, entity_ref: _SceneEntityRef, vector: Vector3) -> None:
        if self._project is None:
            return
        snapped = self._snap_vector(vector)
        project = self._model_editor_service.require_current_project()
        if entity_ref.kind == "geometry":
            geometry = copy.deepcopy(project.model.geometry[entity_ref.index])
            self._model_editor_service.update_geometry(
                entity_ref.index,
                self._move_geometry_to_anchor(geometry, snapped),
            )
            return
        if entity_ref.kind == "source":
            source = copy.deepcopy(project.model.sources[entity_ref.index])
            source.position_m = snapped
            self._model_editor_service.update_source(entity_ref.index, source)
            return
        if entity_ref.kind == "receiver":
            receiver = copy.deepcopy(project.model.receivers[entity_ref.index])
            receiver.position_m = snapped
            self._model_editor_service.update_receiver(entity_ref.index, receiver)
            return
        if entity_ref.kind == "antenna":
            antenna = copy.deepcopy(project.model.antenna_models[entity_ref.index])
            antenna.position_m = snapped
            self._model_editor_service.update_antenna_model(entity_ref.index, antenna)
            return
        geometry_import = copy.deepcopy(project.model.geometry_imports[entity_ref.index])
        geometry_import.position_m = snapped
        self._model_editor_service.update_geometry_import(entity_ref.index, geometry_import)

    def _geometry_anchor_position(self, geometry: GeometryPrimitive) -> QPointF:
        return self._project_point(self._geometry_center(geometry))

    def _geometry_center(self, geometry: GeometryPrimitive) -> Vector3:
        if geometry.kind == "sphere":
            center = geometry.parameters.get("center_m", {})
            return Vector3(
                x=float(center.get("x", 0.0)),
                y=float(center.get("y", 0.0)),
                z=float(center.get("z", 0.0)),
            )
        if geometry.kind == "cylinder":
            start = geometry.parameters.get("start_m", {})
            end = geometry.parameters.get("end_m", {})
            return Vector3(
                x=(float(start.get("x", 0.0)) + float(end.get("x", 0.0))) / 2,
                y=(float(start.get("y", 0.0)) + float(end.get("y", 0.0))) / 2,
                z=(float(start.get("z", 0.0)) + float(end.get("z", 0.0))) / 2,
            )
        lower = geometry.parameters.get("lower_left_m", {})
        upper = geometry.parameters.get("upper_right_m", {})
        return Vector3(
            x=(float(lower.get("x", 0.0)) + float(upper.get("x", 0.0))) / 2,
            y=(float(lower.get("y", 0.0)) + float(upper.get("y", 0.0))) / 2,
            z=(float(lower.get("z", 0.0)) + float(upper.get("z", 0.0))) / 2,
        )

    def _move_geometry_to_anchor(self, geometry: GeometryPrimitive, vector: Vector3) -> GeometryPrimitive:
        center = self._geometry_center(geometry)
        delta = Vector3(
            x=vector.x - center.x,
            y=vector.y - center.y,
            z=vector.z - center.z,
        )
        if geometry.kind == "sphere":
            geometry.parameters["center_m"] = {"x": vector.x, "y": vector.y, "z": vector.z}
            return geometry
        if geometry.kind == "cylinder":
            start = geometry.parameters.get("start_m", {})
            end = geometry.parameters.get("end_m", {})
            geometry.parameters["start_m"] = {
                "x": float(start.get("x", 0.0)) + delta.x,
                "y": float(start.get("y", 0.0)) + delta.y,
                "z": float(start.get("z", 0.0)) + delta.z,
            }
            geometry.parameters["end_m"] = {
                "x": float(end.get("x", 0.0)) + delta.x,
                "y": float(end.get("y", 0.0)) + delta.y,
                "z": float(end.get("z", 0.0)) + delta.z,
            }
            return geometry
        lower = geometry.parameters.get("lower_left_m", {})
        upper = geometry.parameters.get("upper_right_m", {})
        geometry.parameters["lower_left_m"] = {
            "x": float(lower.get("x", 0.0)) + delta.x,
            "y": float(lower.get("y", 0.0)) + delta.y,
            "z": float(lower.get("z", 0.0)) + delta.z,
        }
        geometry.parameters["upper_right_m"] = {
            "x": float(upper.get("x", 0.0)) + delta.x,
            "y": float(upper.get("y", 0.0)) + delta.y,
            "z": float(upper.get("z", 0.0)) + delta.z,
        }
        return geometry

    def _plane_limits(self, project: Project) -> tuple[float, float]:
        domain = project.model.domain.size_m
        if self._plane == "xz":
            return domain.x, domain.z
        if self._plane == "yz":
            return domain.y, domain.z
        return domain.x, domain.y

    def _project_point(self, vector: Vector3) -> QPointF:
        if self._plane == "xz":
            return QPointF(vector.x, vector.z)
        if self._plane == "yz":
            return QPointF(vector.y, vector.z)
        return QPointF(vector.x, vector.y)

    def _parameters_point(self, value: dict[str, object]) -> QPointF:
        return self._project_point(
            Vector3(
                x=float(value.get("x", 0.0)),
                y=float(value.get("y", 0.0)),
                z=float(value.get("z", 0.0)),
            )
        )

    def _vector_from_scene_point(self, point: QPointF) -> Vector3:
        project = self._model_editor_service.require_current_project()
        domain = project.model.domain.size_m
        if self._plane == "xz":
            return self._snap_vector(Vector3(x=point.x(), y=domain.y * 0.5, z=point.y()))
        if self._plane == "yz":
            return self._snap_vector(Vector3(x=domain.x * 0.5, y=point.x(), z=point.y()))
        return self._snap_vector(Vector3(x=point.x(), y=point.y(), z=domain.z * 0.5))

    def _snap_vector(self, vector: Vector3) -> Vector3:
        if not self._snap_to_grid.isChecked():
            return vector
        step = self._grid_step.value()
        return Vector3(
            x=round(vector.x / step) * step,
            y=round(vector.y / step) * step,
            z=round(vector.z / step) * step,
        )

    def _selection_signature(self) -> tuple[str, int] | None:
        if self._selected_entity_ref is None:
            return None
        return self._selected_entity_ref.kind, self._selected_entity_ref.index

    def _restore_selection(self, signature: tuple[str, int] | None) -> None:
        if signature is None:
            self._load_entity_details(None)
            return
        self._set_selected_row(signature[0], signature[1])

    def _set_selected_row(self, kind: str, index: int) -> None:
        for row in range(self._entity_list.count()):
            entity_ref = self._entity_list.item(row).data(Qt.ItemDataRole.UserRole)
            if entity_ref.kind == kind and entity_ref.index == index:
                self._entity_list.setCurrentRow(row)
                return
        self._load_entity_details(None)

    def _entity_for_ref(self, entity_ref: _SceneEntityRef):
        project = self._model_editor_service.require_current_project()
        if entity_ref.kind == "geometry":
            return project.model.geometry[entity_ref.index]
        if entity_ref.kind == "source":
            return project.model.sources[entity_ref.index]
        if entity_ref.kind == "receiver":
            return project.model.receivers[entity_ref.index]
        if entity_ref.kind == "antenna":
            return project.model.antenna_models[entity_ref.index]
        return project.model.geometry_imports[entity_ref.index]

    def _entity_position(self, entity_ref: _SceneEntityRef, entity) -> Vector3:
        if entity_ref.kind == "geometry":
            return self._geometry_center(entity)
        return entity.position_m

    def _grid_spacing_for_scene(self, width: float, height: float) -> float:
        base = max(min(width, height), 0.001)
        return _nice_step(base / 8.0)

    def _update_rulers(self, width: float, height: float) -> None:
        axis_x, axis_y = self._plane_axes()
        self._horizontal_ruler.set_scale(0.0, max(width, 0.001), axis_x)
        self._vertical_ruler.set_scale(0.0, max(height, 0.001), axis_y)

    def _plane_axes(self) -> tuple[str, str]:
        if self._plane == "xz":
            return "X", "Z"
        if self._plane == "yz":
            return "Y", "Z"
        return "X", "Y"
