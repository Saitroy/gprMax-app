from __future__ import annotations

import copy
from dataclasses import dataclass
from math import ceil, floor, hypot, log10

from PySide6.QtCore import QMimeData, QPointF, QRectF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDrag, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGraphicsEllipseItem,
    QGridLayout,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsObject,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.models import GeometryPrimitive, Project, Vector3
from ...layouts.flow_layout import FlowLayout
from .helpers import (
    build_float_spinbox,
    build_status_label,
    join_messages,
    parse_csv_values,
)


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
    empty_context_requested = Signal(float, float, object)
    empty_clicked = Signal(float, float)

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
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

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

    def wheelEvent(self, event) -> None:  # noqa: N802
        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self.scale(factor, factor)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        scene = self.scene()
        if scene is not None and not scene.sceneRect().isNull():
            self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        if self.itemAt(event.pos()) is None:
            point = self.mapToScene(event.pos())
            self.empty_context_requested.emit(point.x(), point.y(), event.globalPos())
            event.accept()
            return
        super().contextMenuEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.itemAt(event.pos()) is None:
            point = self.mapToScene(event.pos())
            self.empty_clicked.emit(point.x(), point.y())
        super().mouseReleaseEvent(event)


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


class _SceneEntityItem(QGraphicsObject):
    def __init__(
        self,
        entity_ref: _SceneEntityRef,
        *,
        color: QColor,
        shape: str,
        bounds: QRectF,
        label: str,
        on_select,
        on_release,
        on_context_menu,
        line_points: tuple[QPointF, QPointF] | None = None,
        ignores_transform: bool = False,
        secondary_label: str = "",
    ) -> None:
        super().__init__()
        self.entity_ref = entity_ref
        self._color = color
        self._shape = shape
        self._bounds = bounds
        self._label = label
        self._secondary_label = secondary_label
        self._line_points = line_points
        self._on_select = on_select
        self._on_release = on_release
        self._on_context_menu = on_context_menu
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        if ignores_transform:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setZValue(20)
        self.setAcceptHoverEvents(True)
        self._hovered = False

    def boundingRect(self) -> QRectF:
        return self._bounds.adjusted(-18.0, -18.0, 18.0, 38.0)

    def set_movable(self, movable: bool) -> None:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, movable)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        pen = QPen(self._color.darker(120), 2.2 if self.isSelected() else 1.5)
        brush_color = QColor(self._color)
        if self.isSelected():
            brush_color.setAlpha(190)
        elif self._hovered:
            brush_color.setAlpha(155)
        else:
            brush_color.setAlpha(110 if self._shape in {"rect", "ellipse", "line"} else 220)
        painter.setPen(pen)
        painter.setBrush(QBrush(brush_color))
        visual_rect = self._bounds
        if self._shape == "diamond":
            path = QPainterPath()
            path.moveTo(visual_rect.center().x(), visual_rect.top())
            path.lineTo(visual_rect.right(), visual_rect.center().y())
            path.lineTo(visual_rect.center().x(), visual_rect.bottom())
            path.lineTo(visual_rect.left(), visual_rect.center().y())
            path.closeSubpath()
            painter.drawPath(path)
        elif self._shape == "triangle":
            path = QPainterPath()
            path.moveTo(visual_rect.center().x(), visual_rect.top())
            path.lineTo(visual_rect.right(), visual_rect.bottom())
            path.lineTo(visual_rect.left(), visual_rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)
        elif self._shape == "rect":
            painter.drawRect(visual_rect)
        elif self._shape == "line" and self._line_points is not None:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(self._line_points[0], self._line_points[1])
        else:
            painter.drawEllipse(visual_rect)

        painter.setPen(QColor("#223341"))
        label_rect = QRectF(
            visual_rect.left(),
            visual_rect.bottom() + 4.0,
            max(150.0, visual_rect.width() + 40.0),
            16.0,
        )
        painter.drawText(label_rect, self._label)
        if self._secondary_label:
            painter.setPen(QColor("#5b6f80"))
            painter.drawText(
                QRectF(
                    label_rect.left(),
                    label_rect.bottom() + 2.0,
                    label_rect.width(),
                    16.0,
                ),
                self._secondary_label,
            )

    def mousePressEvent(self, event) -> None:
        self._on_select(self.entity_ref)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self._on_release(self.entity_ref, self.scenePos())

    def contextMenuEvent(self, event) -> None:
        self._on_select(self.entity_ref)
        self._on_context_menu(self.entity_ref, event.screenPos())
        event.accept()

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)


class _SceneResizeHandle(QGraphicsObject):
    def __init__(
        self,
        role: str,
        *,
        color: QColor,
        on_select,
        on_move,
        on_release,
    ) -> None:
        super().__init__()
        self.role = role
        self._color = color
        self._on_select = on_select
        self._on_move = on_move
        self._on_release = on_release
        self._hovered = False
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(60)

    def boundingRect(self) -> QRectF:
        return QRectF(-6.0, -6.0, 12.0, 12.0)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setPen(QPen(self._color.darker(135), 1.6))
        fill = QColor(self._color)
        fill.setAlpha(240 if self._hovered else 200)
        painter.setBrush(QBrush(fill))
        painter.drawRect(self.boundingRect())

    def mousePressEvent(self, event) -> None:
        self._on_select()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self._on_release(self.role, self.scenePos())

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        self._on_move(self.role, self.scenePos())

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)


class SceneCanvasPanel(QWidget):
    model_changed = Signal()
    edit_requested = Signal(str)

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
        self._scene_tool = "select"
        self._scene_mode = "move"
        self._active_creation_kind = "box"
        self._selected_entity_ref: _SceneEntityRef | None = None
        self._entity_items: dict[tuple[str, int], _SceneEntityItem] = {}
        self._resize_handles: list[_SceneResizeHandle] = []
        self._preview_items: list[QGraphicsItem] = []
        self._measurement_items: list[QGraphicsItem] = []
        self._measurement_start: QPointF | None = None
        self._loading = False

        self._plane_combo = QComboBox()
        self._plane_combo.currentIndexChanged.connect(self._change_plane)
        self._scene_tool_combo = QComboBox()
        self._scene_tool_combo.currentIndexChanged.connect(self._change_scene_tool)
        self._scene_mode_combo = QComboBox()
        self._scene_mode_combo.currentIndexChanged.connect(self._change_scene_mode)
        self._snap_to_grid = QCheckBox()
        self._snap_to_grid.toggled.connect(self._refresh_scene)
        self._grid_step = build_float_spinbox(minimum=0.001, maximum=10.0, decimals=4, step=0.001)
        self._grid_step.setValue(0.01)
        self._grid_step.valueChanged.connect(self._refresh_scene)
        self._domain_x = build_float_spinbox(minimum=0.001, maximum=1000.0, decimals=4, step=0.01)
        self._domain_y = build_float_spinbox(minimum=0.001, maximum=1000.0, decimals=4, step=0.01)
        self._domain_z = build_float_spinbox(minimum=0.001, maximum=1000.0, decimals=4, step=0.01)
        self._apply_domain_button = QPushButton()
        self._apply_domain_button.clicked.connect(self._apply_domain_changes)
        self._fit_scene_button = QPushButton()
        self._fit_scene_button.clicked.connect(self._fit_scene)

        self._entity_list = QListWidget()
        self._entity_list.currentRowChanged.connect(self._select_entity_from_list)
        self._status_label = build_status_label("")
        self._hint_label = QLabel()
        self._hint_label.setWordWrap(True)

        self._scene = QGraphicsScene(self)
        self._view = _CanvasView()
        self._view.setScene(self._scene)
        self._view.entity_dropped.connect(self._on_entity_dropped)
        self._view.empty_context_requested.connect(self._show_canvas_context_menu)
        self._view.empty_clicked.connect(self._handle_empty_scene_click)
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
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, kind=entity_kind: self._handle_palette_click(kind)
            )
            self._palette_buttons.append(button)
            buttons_layout.addWidget(button)
        palette_layout.addLayout(buttons_layout)

        self._selected_label = QLabel()
        self._selected_label.setWordWrap(True)
        self._entity_kind_label = QLabel()
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
        self._domain_title = QLabel()
        self._domain_x_label = QLabel()
        self._domain_y_label = QLabel()
        self._domain_z_label = QLabel()
        self._scene_tool_label = QLabel()
        self._scene_mode_label = QLabel()
        self._object_type_label = QLabel()
        self._material_label = QLabel()
        self._waveform_label = QLabel()
        self._axis_label = QLabel()
        self._outputs_label = QLabel()
        self._size_x_label = QLabel()
        self._size_y_label = QLabel()
        self._size_z_label = QLabel()
        self._radius_label = QLabel()
        self._inspector_status = QLabel()
        self._material_combo = QComboBox()
        self._waveform_combo = QComboBox()
        self._axis_combo = QComboBox()
        for axis in ("x", "y", "z"):
            self._axis_combo.addItem(axis, axis)
        self._outputs_edit = QLineEdit()
        self._size_x = build_float_spinbox(minimum=0.0, maximum=1000.0, decimals=4, step=0.01)
        self._size_y = build_float_spinbox(minimum=0.0, maximum=1000.0, decimals=4, step=0.01)
        self._size_z = build_float_spinbox(minimum=0.0, maximum=1000.0, decimals=4, step=0.01)
        self._radius = build_float_spinbox(minimum=0.0, maximum=1000.0, decimals=4, step=0.01)
        self._details_stack = QStackedWidget()
        self._details_empty = QWidget()
        self._details_geometry = QWidget()
        self._details_source = QWidget()
        self._details_receiver = QWidget()
        self._details_generic = QWidget()
        self._build_detail_pages()

        inspector = QFrame()
        inspector.setObjectName("ViewCard")
        inspector_layout = QVBoxLayout(inspector)
        inspector_layout.setContentsMargins(12, 12, 12, 12)
        inspector_layout.setSpacing(10)
        self._inspector_title = QLabel()
        inspector_layout.addWidget(self._inspector_title)
        inspector_layout.addWidget(self._selected_label)
        inspector_layout.addWidget(self._entity_kind_label)
        inspector_form = QFormLayout()
        inspector_form.addRow(self._pos_x_label, self._pos_x)
        inspector_form.addRow(self._pos_y_label, self._pos_y)
        inspector_form.addRow(self._pos_z_label, self._pos_z)
        inspector_form.addRow(self._nudge_step_label, self._nudge_step)
        inspector_layout.addLayout(inspector_form)
        inspector_layout.addWidget(self._details_stack)
        self._nudge_layout = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        inspector_layout.addLayout(self._nudge_layout)
        self._action_layout = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        self._action_layout.addWidget(self._apply_button)
        self._action_layout.addWidget(self._duplicate_button)
        self._action_layout.addWidget(self._delete_button)
        inspector_layout.addLayout(self._action_layout)
        inspector_layout.addWidget(self._inspector_status)

        domain_card = QFrame()
        domain_card.setObjectName("ViewCard")
        domain_layout = QVBoxLayout(domain_card)
        domain_layout.setContentsMargins(12, 12, 12, 12)
        domain_layout.setSpacing(10)
        domain_layout.addWidget(self._domain_title)
        domain_form = QFormLayout()
        domain_form.addRow(self._domain_x_label, self._domain_x)
        domain_form.addRow(self._domain_y_label, self._domain_y)
        domain_form.addRow(self._domain_z_label, self._domain_z)
        domain_layout.addLayout(domain_form)
        domain_actions = FlowLayout(horizontal_spacing=8, vertical_spacing=8)
        domain_actions.addWidget(self._apply_domain_button)
        domain_layout.addLayout(domain_actions)

        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        plane_row = QHBoxLayout()
        self._plane_label = QLabel()
        plane_row.addWidget(self._plane_label)
        plane_row.addWidget(self._plane_combo)
        side_layout.addLayout(plane_row)
        tool_row = QHBoxLayout()
        tool_row.addWidget(self._scene_tool_label)
        tool_row.addWidget(self._scene_tool_combo, 1)
        side_layout.addLayout(tool_row)
        mode_row = QHBoxLayout()
        mode_row.addWidget(self._scene_mode_label)
        mode_row.addWidget(self._scene_mode_combo, 1)
        mode_row.addWidget(self._fit_scene_button)
        side_layout.addLayout(mode_row)
        snap_form = QFormLayout()
        self._grid_step_label_global = QLabel()
        snap_form.addRow("", self._snap_to_grid)
        snap_form.addRow(self._grid_step_label_global, self._grid_step)
        side_layout.addLayout(snap_form)
        side_layout.addWidget(self._hint_label)
        side_layout.addWidget(domain_card)
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

    def _build_detail_pages(self) -> None:
        empty_layout = QVBoxLayout(self._details_empty)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.addWidget(QLabel(""))

        geometry_form = QFormLayout(self._details_geometry)
        geometry_form.addRow(self._material_label, self._material_combo)
        geometry_form.addRow(self._size_x_label, self._size_x)
        geometry_form.addRow(self._size_y_label, self._size_y)
        geometry_form.addRow(self._size_z_label, self._size_z)
        geometry_form.addRow(self._radius_label, self._radius)

        source_form = QFormLayout(self._details_source)
        source_form.addRow(self._axis_label, self._axis_combo)
        source_form.addRow(self._waveform_label, self._waveform_combo)

        receiver_form = QFormLayout(self._details_receiver)
        receiver_form.addRow(self._outputs_label, self._outputs_edit)

        generic_layout = QVBoxLayout(self._details_generic)
        generic_layout.setContentsMargins(0, 0, 0, 0)
        generic_layout.addWidget(QLabel(""))

        self._details_stack.addWidget(self._details_empty)
        self._details_stack.addWidget(self._details_geometry)
        self._details_stack.addWidget(self._details_source)
        self._details_stack.addWidget(self._details_receiver)
        self._details_stack.addWidget(self._details_generic)

        self._material_combo.currentIndexChanged.connect(self._apply_entity_changes)
        self._waveform_combo.currentIndexChanged.connect(self._apply_entity_changes)
        self._axis_combo.currentIndexChanged.connect(self._apply_entity_changes)
        self._outputs_edit.textChanged.connect(self._apply_entity_changes)
        for widget in (self._size_x, self._size_y, self._size_z, self._radius):
            widget.valueChanged.connect(self._apply_entity_changes)

    def retranslate_ui(self) -> None:
        self._plane_label.setText(self._localization.text("editor.scene.plane"))
        self._scene_tool_label.setText(self._localization.text("editor.scene.tool"))
        self._scene_mode_label.setText(self._localization.text("editor.scene.mode"))
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
        self._domain_title.setText(self._localization.text("editor.scene.domain"))
        self._domain_x_label.setText(self._localization.text("editor.scene.domain_x"))
        self._domain_y_label.setText(self._localization.text("editor.scene.domain_y"))
        self._domain_z_label.setText(self._localization.text("editor.scene.domain_z"))
        self._apply_domain_button.setText(self._localization.text("editor.scene.apply_domain"))
        self._fit_scene_button.setText(self._localization.text("editor.scene.fit"))
        self._object_type_label.setText(self._localization.text("editor.scene.object_type"))
        self._material_label.setText(self._localization.text("editor.geometry.material"))
        self._waveform_label.setText(self._localization.text("editor.sources.waveform"))
        self._axis_label.setText(self._localization.text("editor.sources.axis"))
        self._outputs_label.setText(self._localization.text("editor.receivers.outputs"))
        self._size_x_label.setText(self._localization.text("editor.scene.size_x"))
        self._size_y_label.setText(self._localization.text("editor.scene.size_y"))
        self._size_z_label.setText(self._localization.text("editor.scene.size_z"))
        self._radius_label.setText(self._localization.text("editor.scene.radius"))
        self._outputs_edit.setPlaceholderText(
            self._localization.text("editor.receivers.outputs_placeholder")
        )
        self._inspector_status.setText(self._localization.text("editor.scene.inspector_hint"))
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
        self._scene_tool_combo.blockSignals(True)
        current_tool = self._scene_tool_combo.currentData() or self._scene_tool
        self._scene_tool_combo.clear()
        self._scene_tool_combo.addItem(
            self._localization.text("editor.scene.tool.select"),
            "select",
        )
        self._scene_tool_combo.addItem(
            self._localization.text("editor.scene.tool.create"),
            "create",
        )
        self._scene_tool_combo.addItem(
            self._localization.text("editor.scene.tool.measure"),
            "measure",
        )
        index = self._scene_tool_combo.findData(current_tool)
        self._scene_tool_combo.setCurrentIndex(index if index >= 0 else 0)
        self._scene_tool_combo.blockSignals(False)
        self._scene_mode_combo.blockSignals(True)
        current_mode = self._scene_mode_combo.currentData() or self._scene_mode
        self._scene_mode_combo.clear()
        self._scene_mode_combo.addItem(
            self._localization.text("editor.scene.mode.move"),
            "move",
        )
        self._scene_mode_combo.addItem(
            self._localization.text("editor.scene.mode.resize"),
            "resize",
        )
        index = self._scene_mode_combo.findData(current_mode)
        self._scene_mode_combo.setCurrentIndex(index if index >= 0 else 0)
        self._scene_mode_combo.blockSignals(False)
        for button in self._palette_buttons:
            button.setText(self._localization.text(f"editor.scene.entity.{button.entity_kind}"))
        self._sync_palette_buttons()
        self._refresh_material_choices()
        self._refresh_waveform_choices()
        self.refresh_validation()

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        self._project = project
        self._loading_domain(project)
        self._refresh_material_choices()
        self._refresh_waveform_choices()
        self._loading = False
        self._refresh_scene()
        self.refresh_validation()

    def _loading_domain(self, project: Project | None) -> None:
        enabled = project is not None
        for widget in (self._domain_x, self._domain_y, self._domain_z, self._apply_domain_button):
            widget.setEnabled(enabled)
        if project is None:
            self._domain_x.setValue(1.0)
            self._domain_y.setValue(1.0)
            self._domain_z.setValue(0.1)
            return
        self._domain_x.setValue(project.model.domain.size_m.x)
        self._domain_y.setValue(project.model.domain.size_m.y)
        self._domain_z.setValue(project.model.domain.size_m.z)

    def _refresh_material_choices(self) -> None:
        current_value = self._material_combo.currentData()
        with QSignalBlocker(self._material_combo):
            self._material_combo.clear()
            project = self._model_editor_service.current_project()
            if project is not None:
                for material_id in self._model_editor_service.available_material_ids():
                    self._material_combo.addItem(material_id, material_id)
        index = self._material_combo.findData(current_value)
        if index >= 0:
            self._material_combo.setCurrentIndex(index)
        elif self._material_combo.count() > 0:
            self._material_combo.setCurrentIndex(0)

    def _refresh_waveform_choices(self) -> None:
        current_value = self._waveform_combo.currentData()
        with QSignalBlocker(self._waveform_combo):
            self._waveform_combo.clear()
            self._waveform_combo.addItem(
                self._localization.text("editor.sources.no_waveform"),
                "",
            )
            project = self._model_editor_service.current_project()
            if project is not None:
                for waveform_id in self._model_editor_service.available_waveform_ids():
                    self._waveform_combo.addItem(waveform_id, waveform_id)
        index = self._waveform_combo.findData(current_value)
        if index >= 0:
            self._waveform_combo.setCurrentIndex(index)

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

    def _change_scene_tool(self) -> None:
        self._scene_tool = str(self._scene_tool_combo.currentData() or "select")
        self._view.setDragMode(
            QGraphicsView.DragMode.ScrollHandDrag
            if self._scene_tool == "select"
            else QGraphicsView.DragMode.NoDrag
        )
        self._scene_mode_combo.setEnabled(self._scene_tool == "select")
        if self._scene_tool != "measure":
            self._measurement_start = None
            self._clear_measurement_items()
        if self._scene_tool != "select":
            self._clear_preview_items()
        self._sync_palette_buttons()
        self._refresh_resize_handles()

    def _change_scene_mode(self) -> None:
        self._scene_mode = str(self._scene_mode_combo.currentData() or "move")
        geometry_movable = self._scene_mode != "resize"
        for (kind, _index), item in list(self._entity_items.items()):
            if kind == "geometry":
                item.set_movable(geometry_movable)
        self._refresh_resize_handles()

    def _fit_scene(self) -> None:
        if self._scene.sceneRect().isNull():
            return
        self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _sync_palette_buttons(self) -> None:
        for button in self._palette_buttons:
            button.setChecked(button.entity_kind == self._active_creation_kind)

    def _handle_palette_click(self, entity_kind: str) -> None:
        self._active_creation_kind = entity_kind
        self._sync_palette_buttons()
        if self._scene_tool == "create":
            return
        self._add_entity_at_center(entity_kind)

    def _handle_empty_scene_click(self, scene_x: float, scene_y: float) -> None:
        if self._project is None:
            return
        point = QPointF(scene_x, scene_y)
        if self._scene_tool == "create":
            self._add_entity(self._active_creation_kind, point)
            return
        if self._scene_tool == "measure":
            self._update_measurement(point)

    def _apply_domain_changes(self) -> None:
        project = self._model_editor_service.current_project()
        if project is None:
            return
        self._model_editor_service.update_domain_size(
            Vector3(
                self._domain_x.value(),
                self._domain_y.value(),
                self._domain_z.value(),
            )
        )
        self._refresh_scene()
        self.refresh_validation()
        self.model_changed.emit()

    def _refresh_scene(self) -> None:
        selection = self._selection_signature()
        self._selected_entity_ref = None
        self._clear_resize_handles()
        self._clear_preview_items()
        self._clear_measurement_items()
        self._entity_items.clear()
        with QSignalBlocker(self._entity_list):
            self._entity_list.clear()
        self._scene.clear()
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
            entity_ref = _SceneEntityRef("geometry", index, geometry.label or geometry.kind)
            self._add_entity_item(entity_ref, self._build_geometry_item(entity_ref, geometry))
        for index, source in enumerate(self._project.model.sources):
            entity_ref = _SceneEntityRef("source", index, source.identifier or f"source_{index + 1}")
            self._add_entity_item(
                entity_ref,
                self._build_point_item(
                    entity_ref,
                    self._project_point(source.position_m),
                    QColor("#dc2626"),
                    "triangle",
                ),
            )
        for index, receiver in enumerate(self._project.model.receivers):
            entity_ref = _SceneEntityRef("receiver", index, receiver.identifier or f"receiver_{index + 1}")
            self._add_entity_item(
                entity_ref,
                self._build_point_item(
                    entity_ref,
                    self._project_point(receiver.position_m),
                    QColor("#16a34a"),
                    "ellipse",
                ),
            )
        for index, antenna in enumerate(self._project.model.antenna_models):
            entity_ref = _SceneEntityRef("antenna", index, antenna.identifier or f"antenna_{index + 1}")
            self._add_entity_item(
                entity_ref,
                self._build_point_item(
                    entity_ref,
                    self._project_point(antenna.position_m),
                    QColor("#7c3aed"),
                    "diamond",
                ),
            )
        for index, geometry_import in enumerate(self._project.model.geometry_imports):
            entity_ref = _SceneEntityRef("import", index, geometry_import.identifier or f"import_{index + 1}")
            self._add_entity_item(
                entity_ref,
                self._build_point_item(
                    entity_ref,
                    self._project_point(geometry_import.position_m),
                    QColor("#0f766e"),
                    "ellipse",
                ),
            )
        self._restore_selection(selection)
        self._refresh_resize_handles()
        self._fit_scene()

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

    def _clear_preview_items(self) -> None:
        for item in self._preview_items:
            try:
                if item.scene() is self._scene:
                    self._scene.removeItem(item)
            except RuntimeError:
                continue
        self._preview_items.clear()

    def _clear_measurement_items(self) -> None:
        for item in self._measurement_items:
            try:
                if item.scene() is self._scene:
                    self._scene.removeItem(item)
            except RuntimeError:
                continue
        self._measurement_items.clear()

    def _clear_resize_handles(self) -> None:
        for handle in self._resize_handles:
            try:
                if handle.scene() is self._scene:
                    self._scene.removeItem(handle)
            except RuntimeError:
                continue
        self._resize_handles.clear()

    def _refresh_resize_handles(self) -> None:
        self._clear_resize_handles()
        if (
            self._project is None
            or self._scene_tool != "select"
            or self._scene_mode != "resize"
            or self._selected_entity_ref is None
            or self._selected_entity_ref.kind != "geometry"
        ):
            return
        geometry = self._project.model.geometry[self._selected_entity_ref.index]
        entity_ref = self._selected_entity_ref
        color = self._geometry_color(geometry)
        for role, position in self._geometry_handle_positions(geometry):
            handle = _SceneResizeHandle(
                role,
                color=color,
                on_select=lambda ref=entity_ref: self._select_entity_from_scene(ref),
                on_move=self._preview_geometry_resize,
                on_release=self._resize_geometry_from_handle_release,
            )
            handle.setPos(position)
            self._scene.addItem(handle)
            self._resize_handles.append(handle)

    def _update_measurement(self, point: QPointF) -> None:
        if self._measurement_start is None:
            self._measurement_start = point
            self._render_measurement(point, point)
            return
        self._render_measurement(self._measurement_start, point)
        self._measurement_start = point

    def _render_measurement(self, start: QPointF, end: QPointF) -> None:
        self._clear_measurement_items()
        line = QGraphicsLineItem(start.x(), start.y(), end.x(), end.y())
        line.setPen(QPen(QColor("#2563eb"), 1.6, Qt.PenStyle.DashLine))
        line.setZValue(52)
        self._scene.addItem(line)
        self._measurement_items.append(line)

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = hypot(dx, dy)
        axes = self._plane_axes()
        label = QGraphicsSimpleTextItem(
            self._localization.text(
                "editor.scene.measure.distance",
                distance=f"{distance:.4g}",
                axis_x=axes[0],
                axis_y=axes[1],
                delta_x=f"{abs(dx):.4g}",
                delta_y=f"{abs(dy):.4g}",
            )
        )
        label.setBrush(QBrush(QColor("#1e3a5f")))
        label.setPos((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
        label.setZValue(53)
        self._scene.addItem(label)
        self._measurement_items.append(label)

    def _preview_geometry_resize(self, role: str, point: QPointF) -> None:
        if self._selected_entity_ref is None or self._selected_entity_ref.kind != "geometry":
            return
        project = self._model_editor_service.require_current_project()
        geometry = copy.deepcopy(project.model.geometry[self._selected_entity_ref.index])
        vector = self._vector_from_scene_point(point)
        preview = self._resize_geometry(geometry, role, vector)
        self._render_geometry_preview(preview)

    def _render_geometry_preview(self, geometry: GeometryPrimitive) -> None:
        self._clear_preview_items()
        pen = QPen(QColor("#2563eb"), 1.6, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        brush = QBrush(QColor(37, 99, 235, 28))
        center = self._geometry_anchor_position(geometry)

        if geometry.kind == "box":
            lower = self._parameters_point(geometry.parameters.get("lower_left_m", {}))
            upper = self._parameters_point(geometry.parameters.get("upper_right_m", {}))
            rect = QRectF(
                min(lower.x(), upper.x()),
                min(lower.y(), upper.y()),
                abs(upper.x() - lower.x()),
                abs(upper.y() - lower.y()),
            )
            item = QGraphicsRectItem(rect)
            item.setPen(pen)
            item.setBrush(brush)
            item.setZValue(50)
            self._scene.addItem(item)
            self._preview_items.append(item)
        elif geometry.kind == "sphere":
            radius = float(geometry.parameters.get("radius_m", 0.0))
            item = QGraphicsEllipseItem(
                center.x() - radius,
                center.y() - radius,
                radius * 2,
                radius * 2,
            )
            item.setPen(pen)
            item.setBrush(brush)
            item.setZValue(50)
            self._scene.addItem(item)
            self._preview_items.append(item)
        else:
            start = self._parameters_point(geometry.parameters.get("start_m", {}))
            end = self._parameters_point(geometry.parameters.get("end_m", {}))
            item = QGraphicsLineItem(start.x(), start.y(), end.x(), end.y())
            item.setPen(pen)
            item.setZValue(50)
            self._scene.addItem(item)
            self._preview_items.append(item)

        label = QGraphicsSimpleTextItem(self._geometry_secondary_label(geometry))
        label.setBrush(QBrush(QColor("#1e3a5f")))
        label.setPos(center.x(), center.y())
        label.setZValue(51)
        self._scene.addItem(label)
        self._preview_items.append(label)

    def _add_entity_item(self, entity_ref: _SceneEntityRef, item: _SceneEntityItem) -> None:
        self._entity_items[(entity_ref.kind, entity_ref.index)] = item
        self._scene.addItem(item)
        list_item = QListWidgetItem(f"{self._entity_kind_text(entity_ref.kind)}: {entity_ref.label}")
        list_item.setData(Qt.ItemDataRole.UserRole, entity_ref)
        self._entity_list.addItem(list_item)

    def _select_entity_from_list(self, row: int) -> None:
        if row < 0:
            self._selected_entity_ref = None
            self._load_entity_details(None)
            return
        entity_ref = self._entity_list.item(row).data(Qt.ItemDataRole.UserRole)
        self._selected_entity_ref = entity_ref
        stale_refs: list[tuple[str, int]] = []
        for candidate_ref, item in list(self._entity_items.items()):
            try:
                item.setSelected(candidate_ref == (entity_ref.kind, entity_ref.index))
            except RuntimeError:
                stale_refs.append(candidate_ref)
        for candidate_ref in stale_refs:
            self._entity_items.pop(candidate_ref, None)
        self._load_entity_details(entity_ref)

    def _select_entity_from_scene(self, entity_ref: _SceneEntityRef) -> None:
        self._set_selected_row(entity_ref.kind, entity_ref.index)

    def _show_entity_context_menu(self, entity_ref: _SceneEntityRef, global_pos) -> None:
        menu = QMenu(self)
        edit_action = menu.addAction(self._localization.text("editor.scene.context.edit"))
        duplicate_action = menu.addAction(self._localization.text("common.duplicate"))
        delete_action = menu.addAction(self._localization.text("common.delete"))
        action = menu.exec(global_pos)
        if action is None:
            return
        self._set_selected_row(entity_ref.kind, entity_ref.index)
        if action == edit_action:
            self.edit_requested.emit(entity_ref.kind)
            return
        if action == duplicate_action:
            self._duplicate_selected()
            return
        if action == delete_action:
            self._delete_selected()

    def _show_canvas_context_menu(self, scene_x: float, scene_y: float, global_pos) -> None:
        if self._project is None:
            return
        menu = QMenu(self)
        actions = {
            menu.addAction(self._localization.text("editor.scene.entity.box")): "box",
            menu.addAction(self._localization.text("editor.scene.entity.sphere")): "sphere",
            menu.addAction(self._localization.text("editor.scene.entity.cylinder")): "cylinder",
            menu.addSeparator(): "",
            menu.addAction(self._localization.text("editor.scene.entity.source")): "source",
            menu.addAction(self._localization.text("editor.scene.entity.receiver")): "receiver",
            menu.addAction(self._localization.text("editor.scene.entity.antenna")): "antenna",
            menu.addAction(self._localization.text("editor.scene.entity.import")): "import",
        }
        action = menu.exec(global_pos)
        entity_kind = actions.get(action)
        if entity_kind:
            self._add_entity(entity_kind, QPointF(scene_x, scene_y))

    def _load_entity_details(self, entity_ref: _SceneEntityRef | None) -> None:
        self._loading = True
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
            self._entity_kind_label.clear()
            self._details_stack.setCurrentWidget(self._details_empty)
            for spinbox in (self._pos_x, self._pos_y, self._pos_z):
                spinbox.setValue(0.0)
            self._loading = False
            self._refresh_resize_handles()
            return
        entity = self._entity_for_ref(entity_ref)
        position = self._entity_position(entity_ref, entity)
        self._selected_label.setText(entity_ref.label)
        self._entity_kind_label.setText(
            self._localization.text(
                "editor.scene.selected_type",
                entity_type=self._entity_kind_text(entity_ref.kind),
            )
        )
        self._pos_x.setValue(position.x)
        self._pos_y.setValue(position.y)
        self._pos_z.setValue(position.z)
        self._load_detail_fields(entity_ref, entity)
        self._loading = False
        self._refresh_resize_handles()

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
        if self._loading or self._selected_entity_ref is None:
            return
        self._apply_detail_changes()
        self._apply_entity_position(
            self._selected_entity_ref,
            Vector3(self._pos_x.value(), self._pos_y.value(), self._pos_z.value()),
        )
        self._refresh_scene()
        self._set_selected_row(self._selected_entity_ref.kind, self._selected_entity_ref.index)
        self.refresh_validation()
        self.model_changed.emit()

    def _apply_detail_changes(self) -> None:
        if self._selected_entity_ref is None or self._project is None:
            return
        project = self._model_editor_service.require_current_project()
        entity_ref = self._selected_entity_ref
        if entity_ref.kind == "geometry":
            geometry = copy.deepcopy(project.model.geometry[entity_ref.index])
            material_id = str(self._material_combo.currentData() or "")
            geometry.material_ids = [material_id] if material_id else []
            center = self._geometry_center(geometry)
            if geometry.kind == "box":
                half_x = max(self._size_x.value(), 0.001) / 2
                half_y = max(self._size_y.value(), 0.001) / 2
                half_z = max(self._size_z.value(), 0.001) / 2
                geometry.parameters["lower_left_m"] = {
                    "x": center.x - half_x,
                    "y": center.y - half_y,
                    "z": center.z - half_z,
                }
                geometry.parameters["upper_right_m"] = {
                    "x": center.x + half_x,
                    "y": center.y + half_y,
                    "z": center.z + half_z,
                }
            elif geometry.kind == "sphere":
                geometry.parameters["radius_m"] = max(self._radius.value(), 0.001)
            elif geometry.kind == "cylinder":
                half_x = self._size_x.value() / 2
                half_y = self._size_y.value() / 2
                half_z = self._size_z.value() / 2
                geometry.parameters["start_m"] = {
                    "x": center.x - half_x,
                    "y": center.y - half_y,
                    "z": center.z - half_z,
                }
                geometry.parameters["end_m"] = {
                    "x": center.x + half_x,
                    "y": center.y + half_y,
                    "z": center.z + half_z,
                }
                geometry.parameters["radius_m"] = max(self._radius.value(), 0.001)
            self._model_editor_service.update_geometry(entity_ref.index, geometry)
            return

        if entity_ref.kind == "source":
            source = copy.deepcopy(project.model.sources[entity_ref.index])
            source.axis = str(self._axis_combo.currentData() or source.axis)
            source.waveform_id = str(self._waveform_combo.currentData() or "")
            self._model_editor_service.update_source(entity_ref.index, source)
            return

        if entity_ref.kind == "receiver":
            receiver = copy.deepcopy(project.model.receivers[entity_ref.index])
            receiver.outputs = parse_csv_values(self._outputs_edit.text())
            self._model_editor_service.update_receiver(entity_ref.index, receiver)

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
            constrained = self._constrain_geometry_anchor(geometry, snapped)
            self._model_editor_service.update_geometry(
                entity_ref.index,
                self._move_geometry_to_anchor(geometry, constrained),
            )
            return
        constrained = self._clamp_vector_to_domain(snapped)
        if entity_ref.kind == "source":
            source = copy.deepcopy(project.model.sources[entity_ref.index])
            source.position_m = constrained
            self._model_editor_service.update_source(entity_ref.index, source)
            return
        if entity_ref.kind == "receiver":
            receiver = copy.deepcopy(project.model.receivers[entity_ref.index])
            receiver.position_m = constrained
            self._model_editor_service.update_receiver(entity_ref.index, receiver)
            return
        if entity_ref.kind == "antenna":
            antenna = copy.deepcopy(project.model.antenna_models[entity_ref.index])
            antenna.position_m = constrained
            self._model_editor_service.update_antenna_model(entity_ref.index, antenna)
            return
        geometry_import = copy.deepcopy(project.model.geometry_imports[entity_ref.index])
        geometry_import.position_m = constrained
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
        clamped_x = max(0.0, min(point.x(), self._scene.sceneRect().right()))
        clamped_y = max(0.0, min(point.y(), self._scene.sceneRect().bottom()))
        if self._plane == "xz":
            return self._snap_vector(Vector3(x=clamped_x, y=domain.y * 0.5, z=clamped_y))
        if self._plane == "yz":
            return self._snap_vector(Vector3(x=domain.x * 0.5, y=clamped_x, z=clamped_y))
        return self._snap_vector(Vector3(x=clamped_x, y=clamped_y, z=domain.z * 0.5))

    def _snap_vector(self, vector: Vector3) -> Vector3:
        if not self._snap_to_grid.isChecked():
            return vector
        step = self._grid_step.value()
        return Vector3(
            x=round(vector.x / step) * step,
            y=round(vector.y / step) * step,
            z=round(vector.z / step) * step,
        )

    def _clamp_vector_to_domain(self, vector: Vector3) -> Vector3:
        project = self._model_editor_service.require_current_project()
        domain = project.model.domain.size_m
        return Vector3(
            x=max(0.0, min(vector.x, domain.x)),
            y=max(0.0, min(vector.y, domain.y)),
            z=max(0.0, min(vector.z, domain.z)),
        )

    def _constrain_geometry_anchor(
        self,
        geometry: GeometryPrimitive,
        vector: Vector3,
    ) -> Vector3:
        project = self._model_editor_service.require_current_project()
        domain = project.model.domain.size_m
        center = self._geometry_center(geometry)

        if geometry.kind == "sphere":
            radius = float(geometry.parameters.get("radius_m", 0.0))
            return Vector3(
                x=max(radius, min(vector.x, max(radius, domain.x - radius))),
                y=max(radius, min(vector.y, max(radius, domain.y - radius))),
                z=max(radius, min(vector.z, max(radius, domain.z - radius))),
            )

        if geometry.kind == "box":
            lower = geometry.parameters.get("lower_left_m", {})
            upper = geometry.parameters.get("upper_right_m", {})
            half_x = abs(float(upper.get("x", 0.0)) - float(lower.get("x", 0.0))) / 2
            half_y = abs(float(upper.get("y", 0.0)) - float(lower.get("y", 0.0))) / 2
            half_z = abs(float(upper.get("z", 0.0)) - float(lower.get("z", 0.0))) / 2
            return Vector3(
                x=max(half_x, min(vector.x, max(half_x, domain.x - half_x))),
                y=max(half_y, min(vector.y, max(half_y, domain.y - half_y))),
                z=max(half_z, min(vector.z, max(half_z, domain.z - half_z))),
            )

        if geometry.kind == "cylinder":
            start = geometry.parameters.get("start_m", {})
            end = geometry.parameters.get("end_m", {})
            radius = float(geometry.parameters.get("radius_m", 0.0))
            min_margin_x, max_margin_x = self._cylinder_axis_margins(
                float(start.get("x", 0.0)),
                float(end.get("x", 0.0)),
                center.x,
                radius,
            )
            min_margin_y, max_margin_y = self._cylinder_axis_margins(
                float(start.get("y", 0.0)),
                float(end.get("y", 0.0)),
                center.y,
                radius,
            )
            min_margin_z, max_margin_z = self._cylinder_axis_margins(
                float(start.get("z", 0.0)),
                float(end.get("z", 0.0)),
                center.z,
                radius,
            )
            return Vector3(
                x=max(-min_margin_x, min(vector.x, domain.x - max_margin_x)),
                y=max(-min_margin_y, min(vector.y, domain.y - max_margin_y)),
                z=max(-min_margin_z, min(vector.z, domain.z - max_margin_z)),
            )

        return self._clamp_vector_to_domain(vector)

    def _cylinder_axis_margins(
        self,
        start_value: float,
        end_value: float,
        center_value: float,
        radius: float,
    ) -> tuple[float, float]:
        if abs(start_value - end_value) < 1e-9:
            return start_value - center_value - radius, start_value - center_value + radius
        return min(start_value, end_value) - center_value, max(start_value, end_value) - center_value

    def _plane_axis_keys(self) -> tuple[str, str]:
        if self._plane == "xz":
            return "x", "z"
        if self._plane == "yz":
            return "y", "z"
        return "x", "y"

    def _geometry_handle_positions(self, geometry: GeometryPrimitive) -> list[tuple[str, QPointF]]:
        if geometry.kind == "box":
            lower = self._parameters_point(geometry.parameters.get("lower_left_m", {}))
            upper = self._parameters_point(geometry.parameters.get("upper_right_m", {}))
            left = min(lower.x(), upper.x())
            right = max(lower.x(), upper.x())
            top = min(lower.y(), upper.y())
            bottom = max(lower.y(), upper.y())
            return [
                ("corner_tl", QPointF(left, top)),
                ("corner_tr", QPointF(right, top)),
                ("corner_bl", QPointF(left, bottom)),
                ("corner_br", QPointF(right, bottom)),
            ]
        if geometry.kind == "sphere":
            center = self._geometry_anchor_position(geometry)
            radius = float(geometry.parameters.get("radius_m", 0.0))
            return [("radius", QPointF(center.x() + radius, center.y()))]

        start = self._parameters_point(geometry.parameters.get("start_m", {}))
        end = self._parameters_point(geometry.parameters.get("end_m", {}))
        if abs(start.x() - end.x()) < 1e-9 and abs(start.y() - end.y()) < 1e-9:
            center = self._geometry_anchor_position(geometry)
            radius = float(geometry.parameters.get("radius_m", 0.0))
            return [("radius", QPointF(center.x() + radius, center.y()))]
        return [("start", start), ("end", end)]

    def _resize_geometry_from_handle_release(self, role: str, point: QPointF) -> None:
        if self._selected_entity_ref is None or self._selected_entity_ref.kind != "geometry":
            return
        self._clear_preview_items()
        project = self._model_editor_service.require_current_project()
        geometry = copy.deepcopy(project.model.geometry[self._selected_entity_ref.index])
        vector = self._vector_from_scene_point(point)
        updated = self._resize_geometry(geometry, role, vector)
        self._model_editor_service.update_geometry(self._selected_entity_ref.index, updated)
        self._refresh_scene()
        self._set_selected_row(self._selected_entity_ref.kind, self._selected_entity_ref.index)
        self.refresh_validation()
        self.model_changed.emit()

    def _resize_geometry(
        self,
        geometry: GeometryPrimitive,
        role: str,
        vector: Vector3,
    ) -> GeometryPrimitive:
        project = self._model_editor_service.require_current_project()
        domain = project.model.domain.size_m
        axis_a, axis_b = self._plane_axis_keys()
        min_size = max(self._grid_step.value() if self._snap_to_grid.isChecked() else 0.001, 0.001)

        if geometry.kind == "box":
            center = self._geometry_center(geometry)
            lower = geometry.parameters.get("lower_left_m", {})
            upper = geometry.parameters.get("upper_right_m", {})
            half_sizes = {
                "x": abs(float(upper.get("x", 0.0)) - float(lower.get("x", 0.0))) / 2,
                "y": abs(float(upper.get("y", 0.0)) - float(lower.get("y", 0.0))) / 2,
                "z": abs(float(upper.get("z", 0.0)) - float(lower.get("z", 0.0))) / 2,
            }
            for axis in (axis_a, axis_b):
                margin = max(
                    min(getattr(center, axis), getattr(domain, axis) - getattr(center, axis)),
                    min_size,
                )
                half_sizes[axis] = min(
                    max(abs(getattr(vector, axis) - getattr(center, axis)), min_size),
                    margin,
                )
            geometry.parameters["lower_left_m"] = {
                "x": center.x - half_sizes["x"],
                "y": center.y - half_sizes["y"],
                "z": center.z - half_sizes["z"],
            }
            geometry.parameters["upper_right_m"] = {
                "x": center.x + half_sizes["x"],
                "y": center.y + half_sizes["y"],
                "z": center.z + half_sizes["z"],
            }
            return geometry

        if geometry.kind == "sphere" or role == "radius":
            center = self._geometry_center(geometry)
            radius = max(
                hypot(
                    getattr(vector, axis_a) - getattr(center, axis_a),
                    getattr(vector, axis_b) - getattr(center, axis_b),
                ),
                min_size,
            )
            max_radius = max(
                min(
                    center.x,
                    domain.x - center.x,
                    center.y,
                    domain.y - center.y,
                    center.z,
                    domain.z - center.z,
                ),
                min_size,
            )
            geometry.parameters["radius_m"] = min(radius, max_radius)
            return geometry

        start = Vector3(
            x=float(geometry.parameters.get("start_m", {}).get("x", 0.0)),
            y=float(geometry.parameters.get("start_m", {}).get("y", 0.0)),
            z=float(geometry.parameters.get("start_m", {}).get("z", 0.0)),
        )
        end = Vector3(
            x=float(geometry.parameters.get("end_m", {}).get("x", 0.0)),
            y=float(geometry.parameters.get("end_m", {}).get("y", 0.0)),
            z=float(geometry.parameters.get("end_m", {}).get("z", 0.0)),
        )
        radius = max(float(geometry.parameters.get("radius_m", 0.0)), min_size)
        target = copy.deepcopy(start if role == "start" else end)
        for axis in (axis_a, axis_b):
            margin_min = radius
            margin_max = max(radius, getattr(domain, axis) - radius)
            setattr(target, axis, max(margin_min, min(getattr(vector, axis), margin_max)))
        if role == "start":
            start = target
        else:
            end = target
        if (
            abs(start.x - end.x) < 1e-9
            and abs(start.y - end.y) < 1e-9
            and abs(start.z - end.z) < 1e-9
        ):
            setattr(end, axis_a, min(getattr(domain, axis_a), getattr(end, axis_a) + min_size))
        geometry.parameters["start_m"] = {"x": start.x, "y": start.y, "z": start.z}
        geometry.parameters["end_m"] = {"x": end.x, "y": end.y, "z": end.z}
        geometry.parameters["radius_m"] = radius
        return geometry

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

    def _load_detail_fields(self, entity_ref: _SceneEntityRef, entity) -> None:
        if entity_ref.kind == "geometry":
            self._details_stack.setCurrentWidget(self._details_geometry)
            material_id = entity.material_ids[0] if entity.material_ids else ""
            material_index = self._material_combo.findData(material_id)
            if material_index >= 0:
                self._material_combo.setCurrentIndex(material_index)
            if entity.kind == "box":
                for widget in (self._size_x, self._size_y, self._size_z):
                    widget.setEnabled(True)
                self._radius.setEnabled(False)
                lower = entity.parameters.get("lower_left_m", {})
                upper = entity.parameters.get("upper_right_m", {})
                self._size_x.setValue(abs(float(upper.get("x", 0.0)) - float(lower.get("x", 0.0))))
                self._size_y.setValue(abs(float(upper.get("y", 0.0)) - float(lower.get("y", 0.0))))
                self._size_z.setValue(abs(float(upper.get("z", 0.0)) - float(lower.get("z", 0.0))))
                self._radius.setValue(0.0)
            elif entity.kind == "sphere":
                for widget in (self._size_x, self._size_y, self._size_z):
                    widget.setEnabled(False)
                self._radius.setEnabled(True)
                self._size_x.setValue(0.0)
                self._size_y.setValue(0.0)
                self._size_z.setValue(0.0)
                self._radius.setValue(float(entity.parameters.get("radius_m", 0.0)))
            else:
                for widget in (self._size_x, self._size_y, self._size_z, self._radius):
                    widget.setEnabled(True)
                start = entity.parameters.get("start_m", {})
                end = entity.parameters.get("end_m", {})
                self._size_x.setValue(abs(float(end.get("x", 0.0)) - float(start.get("x", 0.0))))
                self._size_y.setValue(abs(float(end.get("y", 0.0)) - float(start.get("y", 0.0))))
                self._size_z.setValue(abs(float(end.get("z", 0.0)) - float(start.get("z", 0.0))))
                self._radius.setValue(float(entity.parameters.get("radius_m", 0.0)))
            return

        if entity_ref.kind == "source":
            self._details_stack.setCurrentWidget(self._details_source)
            self._axis_combo.setCurrentText(entity.axis)
            waveform_index = self._waveform_combo.findData(entity.waveform_id)
            self._waveform_combo.setCurrentIndex(waveform_index if waveform_index >= 0 else 0)
            return

        if entity_ref.kind == "receiver":
            self._details_stack.setCurrentWidget(self._details_receiver)
            self._outputs_edit.setText(", ".join(entity.outputs))
            return

        self._details_stack.setCurrentWidget(self._details_generic)

    def _entity_kind_text(self, kind: str) -> str:
        mapping = {
            "geometry": self._localization.text("project.section.geometry"),
            "source": self._localization.text("project.section.sources"),
            "receiver": self._localization.text("project.section.receivers"),
            "antenna": self._localization.text("editor.scene.entity.antenna"),
            "import": self._localization.text("editor.scene.entity.import"),
        }
        return mapping.get(kind, kind.capitalize())

    def _geometry_color(self, geometry: GeometryPrimitive) -> QColor:
        fallback = {
            "box": QColor("#5b8aa5"),
            "sphere": QColor("#8a6fb0"),
            "cylinder": QColor("#b36d4c"),
        }.get(geometry.kind, QColor("#5b8aa5"))
        material_id = geometry.material_ids[0].strip() if geometry.material_ids else ""
        if not material_id:
            return fallback
        palette = (
            "#3f7aa8",
            "#5f8f51",
            "#9b6a4c",
            "#7b63ad",
            "#0f766e",
            "#c1702d",
            "#51719b",
            "#8b5e83",
        )
        color = QColor(palette[sum(ord(char) for char in material_id) % len(palette)])
        return color if color.isValid() else fallback

    def _geometry_secondary_label(self, geometry: GeometryPrimitive) -> str:
        material = geometry.material_ids[0].strip() if geometry.material_ids else self._localization.text("editor.scene.material.none")
        if geometry.kind == "box":
            lower = geometry.parameters.get("lower_left_m", {})
            upper = geometry.parameters.get("upper_right_m", {})
            size_x = abs(float(upper.get("x", 0.0)) - float(lower.get("x", 0.0)))
            size_y = abs(float(upper.get("y", 0.0)) - float(lower.get("y", 0.0)))
            size_z = abs(float(upper.get("z", 0.0)) - float(lower.get("z", 0.0)))
            size = f"{size_x:.3g} x {size_y:.3g} x {size_z:.3g} m"
        elif geometry.kind == "sphere":
            size = f"r={float(geometry.parameters.get('radius_m', 0.0)):.3g} m"
        else:
            start = geometry.parameters.get("start_m", {})
            end = geometry.parameters.get("end_m", {})
            length = hypot(
                hypot(
                    float(end.get("x", 0.0)) - float(start.get("x", 0.0)),
                    float(end.get("y", 0.0)) - float(start.get("y", 0.0)),
                ),
                float(end.get("z", 0.0)) - float(start.get("z", 0.0)),
            )
            radius = float(geometry.parameters.get("radius_m", 0.0))
            size = f"L={length:.3g} m, r={radius:.3g} m"
        return f"{material} | {size}"

    def _build_point_item(
        self,
        entity_ref: _SceneEntityRef,
        position: QPointF,
        color: QColor,
        shape: str,
    ) -> _SceneEntityItem:
        item = _SceneEntityItem(
            entity_ref,
            color=color,
            shape=shape,
            bounds=QRectF(-8.0, -8.0, 16.0, 16.0),
            label=entity_ref.label,
            on_select=self._select_entity_from_scene,
            on_release=self._move_entity_from_anchor,
            on_context_menu=self._show_entity_context_menu,
            ignores_transform=True,
        )
        item.setPos(position)
        return item

    def _build_geometry_item(
        self,
        entity_ref: _SceneEntityRef,
        geometry: GeometryPrimitive,
    ) -> _SceneEntityItem:
        center = self._geometry_anchor_position(geometry)
        color = self._geometry_color(geometry)

        if geometry.kind == "box":
            lower = self._parameters_point(geometry.parameters.get("lower_left_m", {}))
            upper = self._parameters_point(geometry.parameters.get("upper_right_m", {}))
            bounds = QRectF(
                min(lower.x(), upper.x()) - center.x(),
                min(lower.y(), upper.y()) - center.y(),
                abs(upper.x() - lower.x()),
                abs(upper.y() - lower.y()),
            )
            item = _SceneEntityItem(
                entity_ref,
                color=color,
                shape="rect",
                bounds=bounds,
                label=entity_ref.label,
                secondary_label=self._geometry_secondary_label(geometry),
                on_select=self._select_entity_from_scene,
                on_release=self._move_entity_from_anchor,
                on_context_menu=self._show_entity_context_menu,
            )
            item.set_movable(self._scene_mode != "resize")
            item.setPos(center)
            return item

        if geometry.kind == "sphere":
            radius = float(geometry.parameters.get("radius_m", 0.0))
            item = _SceneEntityItem(
                entity_ref,
                color=color,
                shape="ellipse",
                bounds=QRectF(-radius, -radius, radius * 2, radius * 2),
                label=entity_ref.label,
                secondary_label=self._geometry_secondary_label(geometry),
                on_select=self._select_entity_from_scene,
                on_release=self._move_entity_from_anchor,
                on_context_menu=self._show_entity_context_menu,
            )
            item.set_movable(self._scene_mode != "resize")
            item.setPos(center)
            return item

        start = self._parameters_point(geometry.parameters.get("start_m", {}))
        end = self._parameters_point(geometry.parameters.get("end_m", {}))
        radius = float(geometry.parameters.get("radius_m", 0.0))
        rel_start = QPointF(start.x() - center.x(), start.y() - center.y())
        rel_end = QPointF(end.x() - center.x(), end.y() - center.y())
        if abs(rel_start.x() - rel_end.x()) < 1e-9 and abs(rel_start.y() - rel_end.y()) < 1e-9:
            bounds = QRectF(-radius, -radius, radius * 2, radius * 2)
            item = _SceneEntityItem(
                entity_ref,
                color=color,
                shape="ellipse",
                bounds=bounds,
                label=entity_ref.label,
                on_select=self._select_entity_from_scene,
                on_release=self._move_entity_from_anchor,
                on_context_menu=self._show_entity_context_menu,
            )
            item.setPos(center)
            return item

        min_x = min(rel_start.x(), rel_end.x()) - radius
        max_x = max(rel_start.x(), rel_end.x()) + radius
        min_y = min(rel_start.y(), rel_end.y()) - radius
        max_y = max(rel_start.y(), rel_end.y()) + radius
        item = _SceneEntityItem(
            entity_ref,
            color=color,
            shape="line",
            bounds=QRectF(min_x, min_y, max_x - min_x, max_y - min_y),
            label=entity_ref.label,
            secondary_label=self._geometry_secondary_label(geometry),
            on_select=self._select_entity_from_scene,
            on_release=self._move_entity_from_anchor,
            on_context_menu=self._show_entity_context_menu,
            line_points=(rel_start, rel_end),
        )
        item.set_movable(self._scene_mode != "resize")
        item.setPos(center)
        return item

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
