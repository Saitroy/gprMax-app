from __future__ import annotations

import copy
from dataclasses import dataclass
from math import ceil, floor, hypot, log10

from PySide6.QtCore import QMimeData, QPoint, QPointF, QRect, QRectF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QShortcut,
)
from PySide6.QtWidgets import (
    QButtonGroup,
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
    QRubberBand,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QToolButton,
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


@dataclass(slots=True)
class _SceneHandleSpec:
    role: str
    position: QPointF
    handle_kind: str
    label: str = ""


@dataclass(frozen=True, slots=True)
class _SceneHistoryContext:
    selections: tuple[tuple[str, int], ...] = ()
    primary: tuple[str, int] | None = None


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


class _SceneToolbarButton(QToolButton):
    def __init__(self, key: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        self.setObjectName("SceneToolbarButton")
        self.setCheckable(True)
        self.setAutoRaise(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)


class _CanvasView(QGraphicsView):
    entity_dropped = Signal(str, float, float)
    empty_context_requested = Signal(float, float, object)
    empty_clicked = Signal(float, float)
    selection_box_finished = Signal(float, float, float, float, object)
    pointer_moved = Signal(float, float)
    pointer_left = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        self.setMinimumHeight(360)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._selection_enabled = False
        self._selection_origin: QPoint | None = None
        self._selection_modifiers = Qt.KeyboardModifier.NoModifier
        self._selection_band = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())

    def set_selection_enabled(self, enabled: bool) -> None:
        self._selection_enabled = enabled
        if not enabled:
            self._selection_origin = None
            self._selection_band.hide()

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

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._selection_enabled
            and self.itemAt(event.pos()) is None
        ):
            self._selection_origin = event.pos()
            self._selection_modifiers = event.modifiers()
            self._selection_band.setGeometry(QRect(self._selection_origin, self._selection_origin))
            self._selection_band.show()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._selection_origin is not None:
            origin = QPoint(self._selection_origin)
            rect = QRect(origin, event.pos()).normalized()
            self._selection_origin = None
            self._selection_band.hide()
            if rect.width() >= 4 or rect.height() >= 4:
                start = self.mapToScene(rect.topLeft())
                end = self.mapToScene(rect.bottomRight())
                self.selection_box_finished.emit(
                    start.x(),
                    start.y(),
                    end.x(),
                    end.y(),
                    self._selection_modifiers,
                )
            else:
                point = self.mapToScene(event.pos())
                self.empty_clicked.emit(point.x(), point.y())
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self.itemAt(event.pos()) is None:
            point = self.mapToScene(event.pos())
            self.empty_clicked.emit(point.x(), point.y())
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        point = self.mapToScene(event.position().toPoint())
        self.pointer_moved.emit(point.x(), point.y())
        if self._selection_origin is not None:
            self._selection_band.setGeometry(QRect(self._selection_origin, event.pos()).normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.pointer_left.emit()
        super().leaveEvent(event)


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
        super().mousePressEvent(event)
        self._on_select(self.entity_ref, event.modifiers())

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        self._on_release(self.entity_ref, self.scenePos())

    def contextMenuEvent(self, event) -> None:
        self._on_select(self.entity_ref, event.modifiers(), preserve_existing=True)
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
        handle_kind: str,
        color: QColor,
        label: str,
        on_select,
        on_move,
        on_release,
    ) -> None:
        super().__init__()
        self.role = role
        self.handle_kind = handle_kind
        self._color = color
        self._label = label
        self._on_select = on_select
        self._on_move = on_move
        self._on_release = on_release
        self._hovered = False
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(60)
        cursor = Qt.CursorShape.SizeAllCursor
        if handle_kind == "radius":
            cursor = Qt.CursorShape.CrossCursor
        self.setCursor(cursor)

    def boundingRect(self) -> QRectF:
        return QRectF(-8.0, -8.0, 16.0, 16.0)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        pen = QPen(self._color.darker(135), 1.8)
        fill = QColor(self._color)
        fill.setAlpha(245 if self._hovered else 218)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill))
        rect = self.boundingRect().adjusted(1.0, 1.0, -1.0, -1.0)
        if self.handle_kind == "radius":
            path = QPainterPath()
            path.moveTo(rect.center().x(), rect.top())
            path.lineTo(rect.right(), rect.center().y())
            path.lineTo(rect.center().x(), rect.bottom())
            path.lineTo(rect.left(), rect.center().y())
            path.closeSubpath()
            painter.drawPath(path)
        elif self.handle_kind == "endpoint":
            painter.drawEllipse(rect)
        else:
            painter.drawRoundedRect(rect, 3.0, 3.0)
        if self._hovered and self._label:
            painter.setPen(QColor("#ffffff"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._label)

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
        self._selected_entity_refs: list[_SceneEntityRef] = []
        self._entity_items: dict[tuple[str, int], _SceneEntityItem] = {}
        self._resize_handles: list[_SceneResizeHandle] = []
        self._preview_items: list[QGraphicsItem] = []
        self._cursor_items: list[QGraphicsItem] = []
        self._measurement_items: list[QGraphicsItem] = []
        self._measurement_start: QPointF | None = None
        self._cursor_scene_point: QPointF | None = None
        self._drag_anchor_positions: dict[tuple[str, int], QPointF] = {}
        self._selection_syncing = False
        self._loading = False
        self._workbench_mode = False
        self._auxiliary_sidebar_widget: QWidget | None = None

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
        self._fit_scene_button.setObjectName("SceneToolbarAction")

        self._entity_list = QListWidget()
        self._entity_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._entity_list.itemSelectionChanged.connect(self._select_entities_from_list)
        self._status_label = build_status_label("")
        self._hint_label = QLabel()
        self._hint_label.setWordWrap(True)

        self._scene = QGraphicsScene(self)
        self._view = _CanvasView()
        self._view.setScene(self._scene)
        self._view.entity_dropped.connect(self._on_entity_dropped)
        self._view.empty_context_requested.connect(self._show_canvas_context_menu)
        self._view.empty_clicked.connect(self._handle_empty_scene_click)
        self._view.selection_box_finished.connect(self._handle_selection_box)
        self._view.pointer_moved.connect(self._handle_pointer_move)
        self._view.pointer_left.connect(self._handle_pointer_leave)
        self._horizontal_ruler = _MetricRuler(Qt.Orientation.Horizontal)
        self._vertical_ruler = _MetricRuler(Qt.Orientation.Vertical)
        self._scene_toolbar = QFrame()
        self._scene_toolbar.setObjectName("SceneToolbar")
        self._scene_toolbar.setStyleSheet(
            """
            QFrame#SceneToolbar {
                background: rgba(248, 250, 252, 0.96);
                border: 1px solid #d2dbe3;
                border-radius: 16px;
            }
            QLabel[toolbarRole="section"] {
                color: #687a8a;
                font-size: 9pt;
                font-weight: 600;
            }
            QLabel[toolbarRole="status"] {
                color: #405261;
                background: #eef3f7;
                border: 1px solid #d2dbe3;
                border-radius: 10px;
                padding: 6px 10px;
            }
            QToolButton#SceneToolbarButton,
            QPushButton#SceneToolbarAction {
                background: #f7fafc;
                border: 1px solid #c4d1dc;
                border-radius: 10px;
                color: #223341;
                padding: 7px 12px;
                font-weight: 600;
            }
            QToolButton#SceneToolbarButton:hover,
            QPushButton#SceneToolbarAction:hover {
                background: #edf4f8;
                border-color: #9cb0c1;
            }
            QToolButton#SceneToolbarButton:checked {
                background: #dfeef9;
                border-color: #6b93b5;
                color: #1f425c;
            }
            QToolButton#SceneToolbarButton:disabled {
                background: #f1f4f6;
                border-color: #d7dee4;
                color: #8a98a4;
            }
            """
        )
        self._plane_buttons: dict[str, _SceneToolbarButton] = {}
        self._tool_buttons: dict[str, _SceneToolbarButton] = {}
        self._mode_buttons: dict[str, _SceneToolbarButton] = {}
        self._plane_group = QButtonGroup(self)
        self._plane_group.setExclusive(True)
        self._tool_group = QButtonGroup(self)
        self._tool_group.setExclusive(True)
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._toolbar_plane_label = QLabel()
        self._toolbar_plane_label.setProperty("toolbarRole", "section")
        self._toolbar_tool_label = QLabel()
        self._toolbar_tool_label.setProperty("toolbarRole", "section")
        self._toolbar_mode_label = QLabel()
        self._toolbar_mode_label.setProperty("toolbarRole", "section")
        self._toolbar_history_label = QLabel()
        self._toolbar_history_label.setProperty("toolbarRole", "section")
        self._cursor_status_label = QLabel()
        self._cursor_status_label.setProperty("toolbarRole", "status")
        self._undo_button = QPushButton()
        self._undo_button.setObjectName("SceneToolbarAction")
        self._undo_button.clicked.connect(self._undo_scene_change)
        self._redo_button = QPushButton()
        self._redo_button.setObjectName("SceneToolbarAction")
        self._redo_button.clicked.connect(self._redo_scene_change)
        self._build_scene_toolbar()

        self._palette_buttons: list[_PaletteButton] = []
        self._palette_card = QFrame()
        self._palette_card.setObjectName("ViewCard")
        palette_layout = QVBoxLayout(self._palette_card)
        palette_layout.setContentsMargins(12, 12, 12, 12)
        palette_layout.setSpacing(10)
        self._palette_title = QLabel()
        self._palette_title.setObjectName("SectionTitle")
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
        self._domain_card = domain_card
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

        self._entities_card = QFrame()
        self._entities_card.setObjectName("ViewCard")
        entities_layout = QVBoxLayout(self._entities_card)
        entities_layout.setContentsMargins(12, 12, 12, 12)
        entities_layout.setSpacing(10)
        self._plane_label = QLabel()
        snap_form = QFormLayout()
        self._grid_step_label_global = QLabel()
        snap_form.addRow("", self._snap_to_grid)
        snap_form.addRow(self._grid_step_label_global, self._grid_step)
        self._entities_title = QLabel()
        self._entities_title.setObjectName("SectionTitle")
        entities_layout.addWidget(self._entities_title)
        entities_layout.addWidget(self._entity_list, 1)

        self._side_panel = QWidget()
        self._side_layout = QVBoxLayout(self._side_panel)
        self._side_layout.setContentsMargins(0, 0, 0, 0)
        self._side_layout.setSpacing(12)
        self._side_layout.addLayout(snap_form)
        self._side_layout.addWidget(self._hint_label)
        self._side_layout.addWidget(domain_card)
        self._side_layout.addWidget(self._palette_card)
        self._side_layout.addWidget(inspector)
        self._side_layout.addWidget(self._entities_card, 1)
        self._side_layout.addWidget(self._status_label)

        self._side_scroll = QScrollArea()
        self._side_scroll.setWidgetResizable(True)
        self._side_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._side_scroll.setWidget(self._side_panel)
        self._side_scroll.setMinimumWidth(280)
        self._side_scroll.setMaximumWidth(380)
        self._side_scroll.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )

        view_shell = QWidget()
        view_shell_layout = QGridLayout(view_shell)
        view_shell_layout.setContentsMargins(0, 0, 0, 0)
        view_shell_layout.setHorizontalSpacing(0)
        view_shell_layout.setVerticalSpacing(12)
        view_shell_layout.addWidget(self._scene_toolbar, 0, 0, 1, 2)
        corner = QLabel()
        corner.setMinimumSize(52, 32)
        corner.setStyleSheet("background:#edf3f7; border: 1px solid #c7d2db;")
        view_shell_layout.addWidget(corner, 1, 0)
        view_shell_layout.addWidget(self._horizontal_ruler, 1, 1)
        view_shell_layout.addWidget(self._vertical_ruler, 2, 0)
        view_shell_layout.addWidget(self._view, 2, 1)
        view_shell_layout.setColumnStretch(1, 1)
        view_shell_layout.setRowStretch(2, 1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(view_shell, 1)
        layout.addWidget(self._side_scroll, 0)

        self._build_nudge_buttons()
        self.retranslate_ui()
        self.set_project(None)
        self._build_shortcuts()

    def _build_scene_toolbar(self) -> None:
        layout = QHBoxLayout(self._scene_toolbar)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)
        layout.addWidget(self._build_toolbar_section(self._toolbar_plane_label, self._build_plane_buttons()))
        layout.addWidget(self._build_toolbar_section(self._toolbar_tool_label, self._build_tool_buttons()))
        layout.addWidget(self._build_toolbar_section(self._toolbar_mode_label, self._build_mode_buttons()))
        layout.addWidget(
            self._build_toolbar_section(
                self._toolbar_history_label,
                self._build_history_buttons(),
            )
        )
        layout.addStretch(1)
        self._cursor_status_label.setMinimumWidth(180)
        layout.addWidget(self._cursor_status_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._fit_scene_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon))
        layout.addWidget(self._fit_scene_button, 0, Qt.AlignmentFlag.AlignVCenter)

    def _build_toolbar_section(self, title: QLabel, content_layout: QHBoxLayout) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(title)
        layout.addLayout(content_layout)
        return wrapper

    def _build_plane_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for plane_key, label in (("xy", "XY"), ("xz", "XZ"), ("yz", "YZ")):
            button = _SceneToolbarButton(plane_key)
            button.setText(label)
            button.clicked.connect(
                lambda checked=False, key=plane_key: self._set_plane_from_toolbar(key)
            )
            self._plane_group.addButton(button)
            self._plane_buttons[plane_key] = button
            layout.addWidget(button)
        return layout

    def _build_tool_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        specs = (
            ("select", QStyle.StandardPixmap.SP_ArrowForward),
            ("create", QStyle.StandardPixmap.SP_FileDialogNewFolder),
            ("measure", QStyle.StandardPixmap.SP_DialogApplyButton),
        )
        for key, icon in specs:
            button = _SceneToolbarButton(key)
            button.setIcon(self.style().standardIcon(icon))
            button.clicked.connect(lambda checked=False, value=key: self._set_scene_tool_from_toolbar(value))
            self._tool_group.addButton(button)
            self._tool_buttons[key] = button
            layout.addWidget(button)
        return layout

    def _build_mode_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        specs = (
            ("move", QStyle.StandardPixmap.SP_ArrowRight),
            ("resize", QStyle.StandardPixmap.SP_TitleBarMaxButton),
        )
        for key, icon in specs:
            button = _SceneToolbarButton(key)
            button.setIcon(self.style().standardIcon(icon))
            button.clicked.connect(lambda checked=False, value=key: self._set_scene_mode_from_toolbar(value))
            self._mode_group.addButton(button)
            self._mode_buttons[key] = button
            layout.addWidget(button)
        return layout

    def _build_history_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._undo_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self._redo_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        layout.addWidget(self._undo_button)
        layout.addWidget(self._redo_button)
        return layout

    def _build_shortcuts(self) -> None:
        shortcuts = (
            (QKeySequence.StandardKey.Undo, self._handle_undo_shortcut),
            (QKeySequence.StandardKey.Redo, self._handle_redo_shortcut),
            ("Ctrl+Y", self._handle_redo_shortcut),
            (QKeySequence.StandardKey.Delete, self._handle_delete_shortcut),
            ("Ctrl+D", self._handle_duplicate_shortcut),
        )
        self._shortcuts: list[QShortcut] = []
        for key_sequence, handler in shortcuts:
            shortcut = QShortcut(QKeySequence(key_sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def _set_plane_from_toolbar(self, plane: str) -> None:
        index = self._plane_combo.findData(plane)
        if index >= 0:
            self._plane_combo.setCurrentIndex(index)

    def _set_scene_tool_from_toolbar(self, tool: str) -> None:
        index = self._scene_tool_combo.findData(tool)
        if index >= 0:
            self._scene_tool_combo.setCurrentIndex(index)

    def _set_scene_mode_from_toolbar(self, mode: str) -> None:
        index = self._scene_mode_combo.findData(mode)
        if index >= 0:
            self._scene_mode_combo.setCurrentIndex(index)

    def _sync_toolbar_buttons(self) -> None:
        for plane_key, button in self._plane_buttons.items():
            button.setChecked(plane_key == self._plane)
        for tool_key, button in self._tool_buttons.items():
            button.setChecked(tool_key == self._scene_tool)
        mode_enabled = self._scene_tool == "select"
        for mode_key, button in self._mode_buttons.items():
            button.setEnabled(mode_enabled)
            button.setChecked(mode_key == self._scene_mode and mode_enabled)
        self._refresh_history_controls()

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
        self._toolbar_plane_label.setText(self._localization.text("editor.scene.plane"))
        self._toolbar_tool_label.setText(self._localization.text("editor.scene.tool"))
        self._toolbar_mode_label.setText(self._localization.text("editor.scene.mode"))
        self._toolbar_history_label.setText(self._localization.text("editor.scene.history"))
        self._palette_title.setText(self._localization.text("editor.scene.palette"))
        self._entities_title.setText(self._localization.text("editor.scene.entities"))
        self._hint_label.setText(self._localization.text("editor.scene.hint"))
        self._snap_to_grid.setText(self._localization.text("editor.scene.snap"))
        self._grid_step_label_global.setText(self._localization.text("editor.scene.grid_step"))
        self._inspector_title.setText(self._localization.text("editor.scene.inspector"))
        self._apply_button.setText(self._localization.text("editor.scene.apply"))
        self._undo_button.setText(self._localization.text("common.undo"))
        self._redo_button.setText(self._localization.text("common.redo"))
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
        for tool_key, button in self._tool_buttons.items():
            button.setText(self._localization.text(f"editor.scene.tool.{tool_key}"))
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
        for mode_key, button in self._mode_buttons.items():
            button.setText(self._localization.text(f"editor.scene.mode.{mode_key}"))
        for button in self._palette_buttons:
            button.setText(self._localization.text(f"editor.scene.entity.{button.entity_kind}"))
        self._sync_palette_buttons()
        self._sync_toolbar_buttons()
        self._update_cursor_status()
        self._refresh_material_choices()
        self._refresh_waveform_choices()
        self.refresh_validation()
        self._restore_selection(self._current_selection_context())

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        project_changed = project is not self._project
        self._project = project
        if project_changed:
            self._selected_entity_ref = None
            self._selected_entity_refs = []
            self._drag_anchor_positions = {}
        self._loading_domain(project)
        self._refresh_material_choices()
        self._refresh_waveform_choices()
        self._loading = False
        self._view.set_selection_enabled(self._scene_tool == "select")
        self._refresh_scene()
        self.refresh_validation()
        self._refresh_history_controls()

    def set_workbench_mode(self, enabled: bool) -> None:
        self._workbench_mode = enabled
        self._entities_card.setVisible(not enabled)
        self._hint_label.setVisible(not enabled)

    def set_auxiliary_sidebar_widget(self, widget: QWidget | None) -> None:
        if self._auxiliary_sidebar_widget is widget:
            return
        if self._auxiliary_sidebar_widget is not None:
            self._side_layout.removeWidget(self._auxiliary_sidebar_widget)
            self._auxiliary_sidebar_widget.hide()
        self._auxiliary_sidebar_widget = widget
        if widget is None:
            return
        self._side_layout.insertWidget(0, widget)
        widget.show()

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
        self._sync_toolbar_buttons()
        self._refresh_scene()

    def _change_scene_tool(self) -> None:
        self._scene_tool = str(self._scene_tool_combo.currentData() or "select")
        self._view.setDragMode(
            QGraphicsView.DragMode.ScrollHandDrag
            if self._scene_tool == "select"
            else QGraphicsView.DragMode.NoDrag
        )
        self._view.set_selection_enabled(self._scene_tool == "select")
        self._scene_mode_combo.setEnabled(self._scene_tool == "select")
        if self._scene_tool != "measure":
            self._measurement_start = None
            self._clear_measurement_items()
        if self._scene_tool != "select":
            self._clear_preview_items()
        self._sync_palette_buttons()
        self._sync_toolbar_buttons()
        self._refresh_resize_handles()
        self._refresh_pointer_overlays()

    def _change_scene_mode(self) -> None:
        self._scene_mode = str(self._scene_mode_combo.currentData() or "move")
        geometry_movable = self._scene_mode != "resize"
        for (kind, _index), item in list(self._entity_items.items()):
            if kind == "geometry":
                item.set_movable(geometry_movable)
        self._sync_toolbar_buttons()
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
        point = self._clamp_scene_point(QPointF(scene_x, scene_y))
        if self._scene_tool == "create":
            self._add_entity(self._active_creation_kind, point)
            return
        if self._scene_tool == "measure":
            self._update_measurement(point)
            return
        if self._scene_tool == "select":
            self._apply_selection_signatures((), None)

    def _apply_domain_changes(self) -> None:
        project = self._model_editor_service.current_project()
        if project is None:
            return
        selection = self._current_selection_context()
        self._model_editor_service.update_domain_size(
            Vector3(
                self._domain_x.value(),
                self._domain_y.value(),
                self._domain_z.value(),
            ),
            undo_context=selection,
            redo_context=selection,
        )
        self._refresh_scene()
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _refresh_scene(self) -> None:
        selection = self._current_selection_context()
        self._selected_entity_ref = None
        self._selected_entity_refs = []
        self._drag_anchor_positions = {}
        self._clear_resize_handles()
        self._clear_preview_items()
        self._clear_cursor_items()
        self._clear_measurement_items()
        self._entity_items.clear()
        with QSignalBlocker(self._entity_list):
            self._entity_list.clear()
        self._scene.clear()
        if self._project is None:
            self._scene.setSceneRect(QRectF(0, 0, 1, 1))
            self._update_rulers(1.0, 1.0)
            self._restore_selection(selection)
            self._update_cursor_status()
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
        self._refresh_pointer_overlays()

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

    def _clear_cursor_items(self) -> None:
        for item in self._cursor_items:
            try:
                if item.scene() is self._scene:
                    self._scene.removeItem(item)
            except RuntimeError:
                continue
        self._cursor_items.clear()

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
            or not self._has_single_selection()
            or self._selected_entity_ref is None
            or self._selected_entity_ref.kind != "geometry"
        ):
            return
        geometry = self._project.model.geometry[self._selected_entity_ref.index]
        entity_ref = self._selected_entity_ref
        color = self._geometry_color(geometry)
        for spec in self._geometry_handle_positions(geometry):
            handle = _SceneResizeHandle(
                spec.role,
                handle_kind=spec.handle_kind,
                color=color,
                label=spec.label,
                on_select=lambda ref=entity_ref: self._select_entity_from_scene(ref),
                on_move=self._preview_geometry_resize,
                on_release=self._resize_geometry_from_handle_release,
            )
            handle.setPos(spec.position)
            self._scene.addItem(handle)
            self._resize_handles.append(handle)

    def _update_measurement(self, point: QPointF) -> None:
        if self._measurement_start is None:
            self._measurement_start = point
            self._render_measurement(point, point)
            self._update_cursor_status()
            return
        self._render_measurement(self._measurement_start, point)
        self._measurement_start = point
        self._update_cursor_status()

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
            self._measurement_text(start, end)
        )
        label.setBrush(QBrush(QColor("#1e3a5f")))
        label.setPos((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
        label.setZValue(53)
        self._scene.addItem(label)
        self._measurement_items.append(label)

    def _handle_pointer_move(self, scene_x: float, scene_y: float) -> None:
        if self._project is None:
            return
        point = self._clamp_scene_point(QPointF(scene_x, scene_y))
        self._cursor_scene_point = point
        self._render_cursor_overlay(point)
        if self._scene_tool == "measure" and self._measurement_start is not None:
            self._render_measurement(self._measurement_start, point)
        self._update_cursor_status()

    def _handle_pointer_leave(self) -> None:
        self._cursor_scene_point = None
        self._clear_cursor_items()
        self._update_cursor_status()

    def _refresh_pointer_overlays(self) -> None:
        self._clear_cursor_items()
        if self._scene_tool != "measure":
            self._clear_measurement_items()
        if self._cursor_scene_point is not None and self._project is not None:
            point = self._clamp_scene_point(self._cursor_scene_point)
            self._cursor_scene_point = point
            self._render_cursor_overlay(point)
        if (
            self._scene_tool == "measure"
            and self._measurement_start is not None
            and self._project is not None
        ):
            endpoint = self._cursor_scene_point or self._measurement_start
            self._render_measurement(self._measurement_start, endpoint)
        self._update_cursor_status()

    def _clamp_scene_point(self, point: QPointF) -> QPointF:
        rect = self._scene.sceneRect()
        if rect.isNull():
            return point
        return QPointF(
            max(rect.left(), min(point.x(), rect.right())),
            max(rect.top(), min(point.y(), rect.bottom())),
        )

    def _measurement_text(self, start: QPointF, end: QPointF) -> str:
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = hypot(dx, dy)
        axes = self._plane_axes()
        return self._localization.text(
            "editor.scene.measure.distance",
            distance=f"{distance:.4g}",
            axis_x=axes[0],
            axis_y=axes[1],
            delta_x=f"{abs(dx):.4g}",
            delta_y=f"{abs(dy):.4g}",
        )

    def _render_cursor_overlay(self, point: QPointF) -> None:
        self._clear_cursor_items()
        rect = self._scene.sceneRect()
        if rect.isNull():
            return
        pen = QPen(QColor(37, 99, 235, 110), 0.0, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        horizontal = QGraphicsLineItem(rect.left(), point.y(), rect.right(), point.y())
        horizontal.setPen(pen)
        horizontal.setZValue(44)
        self._scene.addItem(horizontal)
        self._cursor_items.append(horizontal)
        vertical = QGraphicsLineItem(point.x(), rect.top(), point.x(), rect.bottom())
        vertical.setPen(pen)
        vertical.setZValue(44)
        self._scene.addItem(vertical)
        self._cursor_items.append(vertical)
        marker = QGraphicsEllipseItem(point.x() - 0.006, point.y() - 0.006, 0.012, 0.012)
        marker.setPen(QPen(QColor("#1d4ed8"), 0))
        marker.setBrush(QBrush(QColor("#60a5fa")))
        marker.setZValue(45)
        self._scene.addItem(marker)
        self._cursor_items.append(marker)
        label = QGraphicsSimpleTextItem(self._cursor_position_text(point))
        label.setBrush(QBrush(QColor("#284053")))
        label.setPos(point.x() + 0.01, point.y() + 0.01)
        label.setZValue(46)
        self._scene.addItem(label)
        self._cursor_items.append(label)

    def _cursor_position_text(self, point: QPointF) -> str:
        axis_x, axis_y = self._plane_axes()
        return self._localization.text(
            "editor.scene.cursor.position",
            axis_x=axis_x,
            axis_y=axis_y,
            value_x=f"{point.x():.4g}",
            value_y=f"{point.y():.4g}",
        )

    def _update_cursor_status(self) -> None:
        if self._project is None or self._cursor_scene_point is None:
            self._cursor_status_label.setText(
                self._localization.text("editor.scene.cursor.idle")
            )
            return
        text = self._cursor_position_text(self._cursor_scene_point)
        if self._scene_tool == "measure" and self._measurement_start is not None:
            text = f"{text} | {self._measurement_text(self._measurement_start, self._cursor_scene_point)}"
        self._cursor_status_label.setText(text)

    def _preview_geometry_resize(self, role: str, point: QPointF) -> None:
        if (
            not self._has_single_selection()
            or self._selected_entity_ref is None
            or self._selected_entity_ref.kind != "geometry"
        ):
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

    def _select_entities_from_list(self) -> None:
        if self._selection_syncing:
            return
        selected_signatures: list[tuple[str, int]] = []
        primary_signature: tuple[str, int] | None = None
        current_item = self._entity_list.currentItem()
        if current_item is not None and current_item.isSelected():
            entity_ref = current_item.data(Qt.ItemDataRole.UserRole)
            primary_signature = self._entity_signature(entity_ref)
        for row in range(self._entity_list.count()):
            item = self._entity_list.item(row)
            if not item.isSelected():
                continue
            entity_ref = item.data(Qt.ItemDataRole.UserRole)
            signature = self._entity_signature(entity_ref)
            selected_signatures.append(signature)
            if primary_signature is None:
                primary_signature = signature
        self._apply_selection_signatures(tuple(selected_signatures), primary_signature)

    def _select_entity_from_scene(
        self,
        entity_ref: _SceneEntityRef,
        modifiers=Qt.KeyboardModifier.NoModifier,
        *,
        preserve_existing: bool = False,
    ) -> None:
        signature = self._entity_signature(entity_ref)
        current_signatures = list(self._selected_signatures())
        current_set = set(current_signatures)
        has_multi_modifier = bool(
            modifiers
            & (
                Qt.KeyboardModifier.ControlModifier
                | Qt.KeyboardModifier.ShiftModifier
            )
        )
        if preserve_existing:
            if signature not in current_set:
                current_signatures.append(signature)
            next_signatures = tuple(current_signatures)
        elif has_multi_modifier:
            if signature in current_set:
                next_signatures = tuple(
                    candidate for candidate in current_signatures if candidate != signature
                )
            else:
                current_signatures.append(signature)
                next_signatures = tuple(current_signatures)
        elif signature in current_set and len(current_signatures) > 1:
            next_signatures = tuple(current_signatures)
        else:
            next_signatures = (signature,)
        self._apply_selection_signatures(
            next_signatures,
            signature if signature in next_signatures else None,
        )
        if signature in set(self._selected_signatures()):
            self._capture_drag_anchor_positions(signature)

    def _show_entity_context_menu(self, entity_ref: _SceneEntityRef, global_pos) -> None:
        menu = QMenu(self)
        edit_action = menu.addAction(self._localization.text("editor.scene.context.edit"))
        duplicate_action = menu.addAction(self._localization.text("common.duplicate"))
        delete_action = menu.addAction(self._localization.text("common.delete"))
        action = menu.exec(global_pos)
        if action is None:
            return
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
        self._selected_entity_refs = [entity_ref] if entity_ref is not None else []
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
        self._inspector_status.setText(self._localization.text("editor.scene.inspector_hint"))
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

    def _load_multi_selection_details(
        self,
        entity_refs: list[_SceneEntityRef],
        primary_ref: _SceneEntityRef | None,
    ) -> None:
        self._loading = True
        self._selected_entity_refs = list(entity_refs)
        self._selected_entity_ref = primary_ref
        for widget in (self._pos_x, self._pos_y, self._pos_z, self._apply_button):
            widget.setEnabled(False)
        for widget in (
            self._nudge_step,
            self._duplicate_button,
            self._delete_button,
            *self._nudge_buttons,
        ):
            widget.setEnabled(True)
        self._selected_label.setText(
            self._localization.text(
                "editor.scene.multiple_selected",
                count=len(entity_refs),
            )
        )
        for spinbox in (self._pos_x, self._pos_y, self._pos_z):
            spinbox.setValue(0.0)
        entity_types = ", ".join(
            sorted({self._entity_kind_text(entity_ref.kind) for entity_ref in entity_refs})
        )
        self._entity_kind_label.setText(
            self._localization.text(
                "editor.scene.multiple_selected_types",
                entity_types=entity_types,
            )
        )
        self._details_stack.setCurrentWidget(self._details_generic)
        self._inspector_status.setText(
            self._localization.text("editor.scene.multiple_selected_hint")
        )
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
        selection_before = self._current_selection_context()
        created_selection: tuple[str, int] | None = None
        with self._model_editor_service.history_batch() as batch:
            batch.undo_context = selection_before
            if entity_kind in {"box", "sphere", "cylinder"}:
                index = self._model_editor_service.add_geometry(kind=entity_kind)
                geometry = copy.deepcopy(project.model.geometry[index])
                self._model_editor_service.update_geometry(
                    index,
                    self._move_geometry_to_anchor(geometry, vector),
                )
                created_selection = ("geometry", index)
            elif entity_kind == "source":
                index = self._model_editor_service.add_source()
                source = copy.deepcopy(project.model.sources[index])
                source.position_m = vector
                self._model_editor_service.update_source(index, source)
                created_selection = ("source", index)
            elif entity_kind == "receiver":
                index = self._model_editor_service.add_receiver()
                receiver = copy.deepcopy(project.model.receivers[index])
                receiver.position_m = vector
                self._model_editor_service.update_receiver(index, receiver)
                created_selection = ("receiver", index)
            elif entity_kind == "antenna":
                index = self._model_editor_service.add_antenna_model()
                antenna = copy.deepcopy(project.model.antenna_models[index])
                antenna.position_m = vector
                self._model_editor_service.update_antenna_model(index, antenna)
                created_selection = ("antenna", index)
            elif entity_kind == "import":
                index = self._model_editor_service.add_geometry_import()
                geometry_import = copy.deepcopy(project.model.geometry_imports[index])
                geometry_import.position_m = vector
                self._model_editor_service.update_geometry_import(index, geometry_import)
                created_selection = ("import", index)
            batch.redo_context = self._selection_context(
                (created_selection,) if created_selection is not None else (),
                created_selection,
            )
        self._refresh_scene()
        if created_selection is not None:
            self._restore_selection(
                self._selection_context((created_selection,), created_selection)
            )
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _move_entity_from_anchor(self, entity_ref: _SceneEntityRef, point: QPointF) -> None:
        if self._project is None:
            return
        selection = self._current_selection_context()
        selection_signatures = self._selected_signatures()
        entity_signature = self._entity_signature(entity_ref)
        if (
            len(selection_signatures) > 1
            and entity_signature in set(selection_signatures)
            and entity_signature in self._drag_anchor_positions
        ):
            delta = point - self._drag_anchor_positions[entity_signature]
            with self._model_editor_service.history_batch() as batch:
                batch.undo_context = selection
                batch.redo_context = selection
                for signature in selection_signatures:
                    selected_ref = self._entity_ref_for_signature(signature)
                    if selected_ref is None:
                        continue
                    anchor = self._drag_anchor_positions.get(signature)
                    if anchor is None:
                        entity = self._entity_for_ref(selected_ref)
                        anchor = self._project_point(
                            self._entity_position(selected_ref, entity)
                        )
                    self._apply_entity_position(
                        selected_ref,
                        self._vector_from_scene_point(anchor + delta),
                    )
        else:
            self._apply_entity_position(
                entity_ref,
                self._vector_from_scene_point(point),
                undo_context=selection,
                redo_context=selection,
            )
        self._drag_anchor_positions = {}
        self._refresh_scene()
        self._restore_selection(selection)
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _apply_entity_changes(self) -> None:
        if self._loading or not self._has_single_selection() or self._selected_entity_ref is None:
            return
        selection = self._current_selection_context()
        with self._model_editor_service.history_batch() as batch:
            batch.undo_context = selection
            batch.redo_context = selection
            self._apply_detail_changes()
            self._apply_entity_position(
                self._selected_entity_ref,
                Vector3(self._pos_x.value(), self._pos_y.value(), self._pos_z.value()),
            )
        self._refresh_scene()
        self._restore_selection(selection)
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _apply_detail_changes(self) -> None:
        if not self._has_single_selection() or self._selected_entity_ref is None or self._project is None:
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
        selected_signatures = self._selected_signatures()
        if not selected_signatures:
            return
        selection_before = self._current_selection_context()
        primary_before = self._primary_selection_signature()
        created_by_signature: dict[tuple[str, int], tuple[str, int]] = {}
        grouped_indices: dict[str, list[int]] = {}
        for kind, index in selected_signatures:
            grouped_indices.setdefault(kind, []).append(index)
        with self._model_editor_service.history_batch() as batch:
            batch.undo_context = selection_before
            for kind, indices in grouped_indices.items():
                offset = 0
                for index in sorted(indices):
                    current_index = index + offset
                    if kind == "geometry":
                        new_index = self._model_editor_service.duplicate_geometry(current_index)
                    elif kind == "source":
                        new_index = self._model_editor_service.duplicate_source(current_index)
                    elif kind == "receiver":
                        new_index = self._model_editor_service.duplicate_receiver(current_index)
                    elif kind == "antenna":
                        new_index = self._model_editor_service.duplicate_antenna_model(
                            current_index
                        )
                    else:
                        new_index = self._model_editor_service.duplicate_geometry_import(
                            current_index
                        )
                    created_by_signature[(kind, index)] = (kind, new_index)
                    offset += 1
            created_selection = tuple(
                created_by_signature[signature]
                for signature in selected_signatures
                if signature in created_by_signature
            )
            primary_selection = (
                created_by_signature.get(primary_before)
                if primary_before is not None
                else None
            )
            if primary_selection is None and created_selection:
                primary_selection = created_selection[-1]
            batch.redo_context = self._selection_context(
                created_selection,
                primary_selection,
            )
        self._refresh_scene()
        self._restore_selection(
            self._selection_context(created_selection, primary_selection)
        )
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _delete_selected(self) -> None:
        selected_signatures = self._selected_signatures()
        if not selected_signatures:
            return
        selection_before = self._current_selection_context()
        next_selection = self._selection_context()
        if len(selected_signatures) == 1:
            next_signature = self._next_selection_after_delete(selected_signatures[0])
            next_selection = self._selection_context(
                (next_signature,) if next_signature is not None else (),
                next_signature,
            )
        grouped_indices: dict[str, list[int]] = {}
        for kind, index in selected_signatures:
            grouped_indices.setdefault(kind, []).append(index)
        with self._model_editor_service.history_batch() as batch:
            batch.undo_context = selection_before
            batch.redo_context = next_selection
            for kind, indices in grouped_indices.items():
                for index in sorted(indices, reverse=True):
                    if kind == "geometry":
                        self._model_editor_service.delete_geometry(index)
                    elif kind == "source":
                        self._model_editor_service.delete_source(index)
                    elif kind == "receiver":
                        self._model_editor_service.delete_receiver(index)
                    elif kind == "antenna":
                        self._model_editor_service.delete_antenna_model(index)
                    else:
                        self._model_editor_service.delete_geometry_import(index)
        self._refresh_scene()
        self._restore_selection(next_selection)
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _nudge_selected(self, dx: int, dy: int, dz: int) -> None:
        selected_signatures = self._selected_signatures()
        if not selected_signatures:
            return
        step = self._nudge_step.value()
        selection = self._current_selection_context()
        with self._model_editor_service.history_batch() as batch:
            batch.undo_context = selection
            batch.redo_context = selection
            for signature in selected_signatures:
                entity_ref = self._entity_ref_for_signature(signature)
                if entity_ref is None:
                    continue
                entity = self._entity_for_ref(entity_ref)
                position = self._entity_position(entity_ref, entity)
                self._apply_entity_position(
                    entity_ref,
                    Vector3(
                        position.x + dx * step,
                        position.y + dy * step,
                        position.z + dz * step,
                    ),
                )
        self._refresh_scene()
        self._restore_selection(selection)
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _apply_entity_position(
        self,
        entity_ref: _SceneEntityRef,
        vector: Vector3,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> None:
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
                undo_context=undo_context,
                redo_context=redo_context,
            )
            return
        constrained = self._clamp_vector_to_domain(snapped)
        if entity_ref.kind == "source":
            source = copy.deepcopy(project.model.sources[entity_ref.index])
            source.position_m = constrained
            self._model_editor_service.update_source(
                entity_ref.index,
                source,
                undo_context=undo_context,
                redo_context=redo_context,
            )
            return
        if entity_ref.kind == "receiver":
            receiver = copy.deepcopy(project.model.receivers[entity_ref.index])
            receiver.position_m = constrained
            self._model_editor_service.update_receiver(
                entity_ref.index,
                receiver,
                undo_context=undo_context,
                redo_context=redo_context,
            )
            return
        if entity_ref.kind == "antenna":
            antenna = copy.deepcopy(project.model.antenna_models[entity_ref.index])
            antenna.position_m = constrained
            self._model_editor_service.update_antenna_model(
                entity_ref.index,
                antenna,
                undo_context=undo_context,
                redo_context=redo_context,
            )
            return
        geometry_import = copy.deepcopy(project.model.geometry_imports[entity_ref.index])
        geometry_import.position_m = constrained
        self._model_editor_service.update_geometry_import(
            entity_ref.index,
            geometry_import,
            undo_context=undo_context,
            redo_context=redo_context,
        )

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

    def _geometry_handle_positions(self, geometry: GeometryPrimitive) -> list[_SceneHandleSpec]:
        if geometry.kind == "box":
            lower = self._parameters_point(geometry.parameters.get("lower_left_m", {}))
            upper = self._parameters_point(geometry.parameters.get("upper_right_m", {}))
            left = min(lower.x(), upper.x())
            right = max(lower.x(), upper.x())
            top = min(lower.y(), upper.y())
            bottom = max(lower.y(), upper.y())
            middle_x = (left + right) / 2
            middle_y = (top + bottom) / 2
            axis_x, axis_y = self._plane_axes()
            return [
                _SceneHandleSpec("corner_tl", QPointF(left, top), "size"),
                _SceneHandleSpec("corner_tr", QPointF(right, top), "size"),
                _SceneHandleSpec("corner_bl", QPointF(left, bottom), "size"),
                _SceneHandleSpec("corner_br", QPointF(right, bottom), "size"),
                _SceneHandleSpec("edge_left", QPointF(left, middle_y), "size", axis_x),
                _SceneHandleSpec("edge_right", QPointF(right, middle_y), "size", axis_x),
                _SceneHandleSpec("edge_top", QPointF(middle_x, top), "size", axis_y),
                _SceneHandleSpec("edge_bottom", QPointF(middle_x, bottom), "size", axis_y),
            ]
        if geometry.kind == "sphere":
            center = self._geometry_anchor_position(geometry)
            radius = float(geometry.parameters.get("radius_m", 0.0))
            return [
                _SceneHandleSpec("radius_e", QPointF(center.x() + radius, center.y()), "radius", "R"),
                _SceneHandleSpec("radius_w", QPointF(center.x() - radius, center.y()), "radius", "R"),
                _SceneHandleSpec("radius_n", QPointF(center.x(), center.y() - radius), "radius", "R"),
                _SceneHandleSpec("radius_s", QPointF(center.x(), center.y() + radius), "radius", "R"),
            ]

        start = self._parameters_point(geometry.parameters.get("start_m", {}))
        end = self._parameters_point(geometry.parameters.get("end_m", {}))
        radius = float(geometry.parameters.get("radius_m", 0.0))
        if abs(start.x() - end.x()) < 1e-9 and abs(start.y() - end.y()) < 1e-9:
            center = self._geometry_anchor_position(geometry)
            return [
                _SceneHandleSpec("radius_e", QPointF(center.x() + radius, center.y()), "radius", "R"),
                _SceneHandleSpec("radius_w", QPointF(center.x() - radius, center.y()), "radius", "R"),
                _SceneHandleSpec("radius_n", QPointF(center.x(), center.y() - radius), "radius", "R"),
                _SceneHandleSpec("radius_s", QPointF(center.x(), center.y() + radius), "radius", "R"),
            ]
        delta_x = end.x() - start.x()
        delta_y = end.y() - start.y()
        length = max(hypot(delta_x, delta_y), 1e-9)
        normal = QPointF(-delta_y / length, delta_x / length)
        middle = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
        return [
            _SceneHandleSpec("start", start, "endpoint", "A"),
            _SceneHandleSpec("end", end, "endpoint", "B"),
            _SceneHandleSpec(
                "radius_pos",
                QPointF(middle.x() + normal.x() * radius, middle.y() + normal.y() * radius),
                "radius",
                "R",
            ),
            _SceneHandleSpec(
                "radius_neg",
                QPointF(middle.x() - normal.x() * radius, middle.y() - normal.y() * radius),
                "radius",
                "R",
            ),
        ]

    def _resize_geometry_from_handle_release(self, role: str, point: QPointF) -> None:
        if (
            not self._has_single_selection()
            or self._selected_entity_ref is None
            or self._selected_entity_ref.kind != "geometry"
        ):
            return
        self._clear_preview_items()
        project = self._model_editor_service.require_current_project()
        geometry = copy.deepcopy(project.model.geometry[self._selected_entity_ref.index])
        vector = self._vector_from_scene_point(point)
        updated = self._resize_geometry(geometry, role, vector)
        selection = self._current_selection_context()
        self._model_editor_service.update_geometry(
            self._selected_entity_ref.index,
            updated,
            undo_context=selection,
            redo_context=selection,
        )
        self._refresh_scene()
        self._restore_selection(selection)
        self.refresh_validation()
        self._refresh_history_controls()
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
            axes_to_resize = (axis_a, axis_b)
            if role in {"edge_left", "edge_right"}:
                axes_to_resize = (axis_a,)
            elif role in {"edge_top", "edge_bottom"}:
                axes_to_resize = (axis_b,)
            for axis in axes_to_resize:
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

        if geometry.kind == "sphere":
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
        if role.startswith("radius"):
            distance = self._distance_to_projected_axis(start, end, vector, axis_a, axis_b)
            geometry.parameters["radius_m"] = min(
                max(distance, min_size),
                self._max_cylinder_radius(start, end, domain, min_size),
            )
            return geometry
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

    def _distance_to_projected_axis(
        self,
        start: Vector3,
        end: Vector3,
        point: Vector3,
        axis_a: str,
        axis_b: str,
    ) -> float:
        start_a = getattr(start, axis_a)
        start_b = getattr(start, axis_b)
        end_a = getattr(end, axis_a)
        end_b = getattr(end, axis_b)
        point_a = getattr(point, axis_a)
        point_b = getattr(point, axis_b)
        delta_a = end_a - start_a
        delta_b = end_b - start_b
        length_sq = delta_a * delta_a + delta_b * delta_b
        if length_sq <= 1e-12:
            return hypot(point_a - start_a, point_b - start_b)
        ratio = ((point_a - start_a) * delta_a + (point_b - start_b) * delta_b) / length_sq
        closest_a = start_a + ratio * delta_a
        closest_b = start_b + ratio * delta_b
        return hypot(point_a - closest_a, point_b - closest_b)

    def _max_cylinder_radius(
        self,
        start: Vector3,
        end: Vector3,
        domain: Vector3,
        min_size: float,
    ) -> float:
        return max(
            min(
                start.x,
                domain.x - start.x,
                end.x,
                domain.x - end.x,
                start.y,
                domain.y - start.y,
                end.y,
                domain.y - end.y,
                start.z,
                domain.z - start.z,
                end.z,
                domain.z - end.z,
            ),
            min_size,
        )

    def _entity_signature(self, entity_ref: _SceneEntityRef) -> tuple[str, int]:
        return entity_ref.kind, entity_ref.index

    def _selection_signature(self) -> tuple[str, int] | None:
        if self._selected_entity_ref is None:
            return None
        return self._entity_signature(self._selected_entity_ref)

    def _selected_signatures(self) -> tuple[tuple[str, int], ...]:
        if self._selected_entity_refs:
            return tuple(self._entity_signature(entity_ref) for entity_ref in self._selected_entity_refs)
        selection = self._selection_signature()
        return (selection,) if selection is not None else ()

    def _primary_selection_signature(self) -> tuple[str, int] | None:
        return self._selection_signature()

    def _has_single_selection(self) -> bool:
        return len(self._selected_signatures()) == 1 and self._selected_entity_ref is not None

    def _selection_context(
        self,
        selections: tuple[tuple[str, int], ...] = (),
        primary: tuple[str, int] | None = None,
    ) -> _SceneHistoryContext:
        normalized: list[tuple[str, int]] = []
        seen: set[tuple[str, int]] = set()
        for signature in selections:
            if signature in seen:
                continue
            normalized.append(signature)
            seen.add(signature)
        if primary is not None and primary not in seen:
            normalized.append(primary)
            seen.add(primary)
        return _SceneHistoryContext(
            selections=tuple(normalized),
            primary=primary if primary in seen else None,
        )

    def _current_selection_context(self) -> _SceneHistoryContext:
        return self._selection_context(
            self._selected_signatures(),
            self._primary_selection_signature(),
        )

    def _selection_from_history_context(
        self,
        context: object | None,
    ) -> _SceneHistoryContext:
        if isinstance(context, _SceneHistoryContext):
            return self._selection_context(context.selections, context.primary)
        if (
            isinstance(context, tuple)
            and len(context) == 2
            and isinstance(context[0], str)
            and isinstance(context[1], int)
        ):
            return self._selection_context((context,), context)
        return self._current_selection_context()

    def _refresh_history_controls(self) -> None:
        enabled = self._project is not None
        self._undo_button.setEnabled(enabled and self._model_editor_service.can_undo())
        self._redo_button.setEnabled(enabled and self._model_editor_service.can_redo())

    def _undo_scene_change(self) -> None:
        result = self._model_editor_service.undo()
        if not result.applied:
            return
        self._loading_domain(self._project)
        self._refresh_material_choices()
        self._refresh_waveform_choices()
        self._refresh_scene()
        self._restore_selection(self._selection_from_history_context(result.context))
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _redo_scene_change(self) -> None:
        result = self._model_editor_service.redo()
        if not result.applied:
            return
        self._loading_domain(self._project)
        self._refresh_material_choices()
        self._refresh_waveform_choices()
        self._refresh_scene()
        self._restore_selection(self._selection_from_history_context(result.context))
        self.refresh_validation()
        self._refresh_history_controls()
        self.model_changed.emit()

    def _focus_blocks_scene_shortcut(self) -> bool:
        return isinstance(self.focusWidget(), QLineEdit)

    def _handle_undo_shortcut(self) -> None:
        if self._focus_blocks_scene_shortcut():
            return
        self._undo_scene_change()

    def _handle_redo_shortcut(self) -> None:
        if self._focus_blocks_scene_shortcut():
            return
        self._redo_scene_change()

    def _handle_delete_shortcut(self) -> None:
        if self._focus_blocks_scene_shortcut():
            return
        self._delete_selected()

    def _handle_duplicate_shortcut(self) -> None:
        if self._focus_blocks_scene_shortcut():
            return
        self._duplicate_selected()

    def _restore_selection(self, context: _SceneHistoryContext) -> None:
        self._apply_selection_signatures(context.selections, context.primary)

    def _set_selected_row(self, kind: str, index: int) -> None:
        self._apply_selection_signatures(((kind, index),), (kind, index))

    def _apply_selection_signatures(
        self,
        signatures: tuple[tuple[str, int], ...],
        primary: tuple[str, int] | None,
    ) -> None:
        context = self._selection_context(signatures, primary)
        target_set = set(context.selections)
        resolved_refs: list[_SceneEntityRef] = []
        self._selection_syncing = True
        try:
            with QSignalBlocker(self._entity_list):
                self._entity_list.clearSelection()
                current_item: QListWidgetItem | None = None
                for row in range(self._entity_list.count()):
                    item = self._entity_list.item(row)
                    entity_ref = item.data(Qt.ItemDataRole.UserRole)
                    signature = self._entity_signature(entity_ref)
                    selected = signature in target_set
                    item.setSelected(selected)
                    if not selected:
                        continue
                    resolved_refs.append(entity_ref)
                    if current_item is None or signature == context.primary:
                        current_item = item
                self._entity_list.setCurrentItem(current_item)
        finally:
            self._selection_syncing = False

        stale_refs: list[tuple[str, int]] = []
        for signature, item in list(self._entity_items.items()):
            try:
                item.setSelected(signature in target_set)
            except RuntimeError:
                stale_refs.append(signature)
        for signature in stale_refs:
            self._entity_items.pop(signature, None)

        primary_ref = None
        if context.primary is not None:
            for entity_ref in resolved_refs:
                if self._entity_signature(entity_ref) == context.primary:
                    primary_ref = entity_ref
                    break
        if primary_ref is None and resolved_refs:
            primary_ref = resolved_refs[-1]
        self._drag_anchor_positions = {}
        if not resolved_refs:
            self._load_entity_details(None)
            return
        if len(resolved_refs) == 1:
            self._load_entity_details(primary_ref)
            return
        self._load_multi_selection_details(resolved_refs, primary_ref)

    def _entity_ref_for_signature(
        self,
        signature: tuple[str, int],
    ) -> _SceneEntityRef | None:
        for row in range(self._entity_list.count()):
            entity_ref = self._entity_list.item(row).data(Qt.ItemDataRole.UserRole)
            if self._entity_signature(entity_ref) == signature:
                return entity_ref
        return None

    def _capture_drag_anchor_positions(
        self,
        primary_signature: tuple[str, int],
    ) -> None:
        if self._project is None or primary_signature not in set(self._selected_signatures()):
            self._drag_anchor_positions = {}
            return
        anchors: dict[tuple[str, int], QPointF] = {}
        for signature in self._selected_signatures():
            entity_ref = self._entity_ref_for_signature(signature)
            if entity_ref is None:
                continue
            entity = self._entity_for_ref(entity_ref)
            anchors[signature] = self._project_point(self._entity_position(entity_ref, entity))
        self._drag_anchor_positions = anchors

    def _handle_selection_box(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        modifiers,
    ) -> None:
        if self._project is None or self._scene_tool != "select":
            return
        selection_rect = QRectF(QPointF(start_x, start_y), QPointF(end_x, end_y)).normalized()
        hit_signatures: list[tuple[str, int]] = []
        stale_refs: list[tuple[str, int]] = []
        for row in range(self._entity_list.count()):
            entity_ref = self._entity_list.item(row).data(Qt.ItemDataRole.UserRole)
            signature = self._entity_signature(entity_ref)
            item = self._entity_items.get(signature)
            if item is None:
                continue
            try:
                if item.sceneBoundingRect().intersects(selection_rect):
                    hit_signatures.append(signature)
            except RuntimeError:
                stale_refs.append(signature)
        for signature in stale_refs:
            self._entity_items.pop(signature, None)
        has_multi_modifier = bool(
            modifiers
            & (
                Qt.KeyboardModifier.ControlModifier
                | Qt.KeyboardModifier.ShiftModifier
            )
        )
        if has_multi_modifier:
            merged_signatures = list(self._selected_signatures())
            existing = set(merged_signatures)
            for signature in hit_signatures:
                if signature in existing:
                    continue
                merged_signatures.append(signature)
                existing.add(signature)
            self._apply_selection_signatures(
                tuple(merged_signatures),
                hit_signatures[-1] if hit_signatures else self._primary_selection_signature(),
            )
            return
        self._apply_selection_signatures(
            tuple(hit_signatures),
            hit_signatures[-1] if hit_signatures else None,
        )

    def _next_selection_after_delete(
        self,
        signature: tuple[str, int],
    ) -> tuple[str, int] | None:
        if self._project is None:
            return None
        kind, index = signature
        if kind == "geometry":
            count = len(self._project.model.geometry)
        elif kind == "source":
            count = len(self._project.model.sources)
        elif kind == "receiver":
            count = len(self._project.model.receivers)
        elif kind == "antenna":
            count = len(self._project.model.antenna_models)
        else:
            count = len(self._project.model.geometry_imports)
        if count <= 1:
            return None
        return kind, min(index, count - 2)

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
