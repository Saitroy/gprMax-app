from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ....application.services.localization_service import LocalizationService
from ....application.services.model_editor_service import ModelEditorService
from ....application.services.validation_service import ValidationService
from ....domain.models import Project
from ....infrastructure.gprmax.command_registry import GprMaxCommandRegistry
from ...splitters import configure_splitter
from .helpers import build_status_label
from .raw_highlighter import GprMaxHighlighter

_PYTHON_BLOCK_DELIMITER = "\n\n# %% block\n\n"


class AdvancedPanel(QWidget):
    model_changed = Signal()

    def __init__(
        self,
        localization: LocalizationService,
        model_editor_service: ModelEditorService,
        validation_service: ValidationService,
        command_registry: GprMaxCommandRegistry,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._model_editor_service = model_editor_service
        self._validation_service = validation_service
        self._command_registry = command_registry
        self._loading = False

        self._category_combo = QComboBox()
        self._category_combo.currentIndexChanged.connect(self._populate_templates)
        self._template_list = QListWidget()
        self._template_list.currentRowChanged.connect(self._update_template_preview)
        self._template_description = QLabel()
        self._template_description.setWordWrap(True)
        self._insert_template_button = QPushButton()
        self._insert_template_button.clicked.connect(self._insert_template)
        self._insert_python_button = QPushButton()
        self._insert_python_button.clicked.connect(self._insert_python_block)

        template_panel = QWidget()
        template_layout = QVBoxLayout(template_panel)
        template_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self._category_label = QLabel()
        form.addRow(self._category_label, self._category_combo)
        template_layout.addLayout(form)
        template_layout.addWidget(self._template_list, 1)
        template_layout.addWidget(self._template_description)
        template_actions = QHBoxLayout()
        template_actions.addWidget(self._insert_template_button)
        template_actions.addWidget(self._insert_python_button)
        template_actions.addStretch(1)
        template_layout.addLayout(template_actions)

        self._raw_editor = QPlainTextEdit()
        self._python_editor = QPlainTextEdit()
        GprMaxHighlighter(self._raw_editor.document())
        GprMaxHighlighter(self._python_editor.document())
        self._raw_editor.textChanged.connect(self._sync_block_lists)
        self._python_editor.textChanged.connect(self._sync_block_lists)

        self._raw_editor_label = QLabel()
        self._python_editor_label = QLabel()
        self._advanced_hint = QLabel()
        self._advanced_hint.setWordWrap(True)
        self._status_label = build_status_label("")
        self._apply_button = QPushButton()
        self._apply_button.clicked.connect(self._apply_changes)

        self._editors_tabs = QTabWidget()
        self._raw_blocks_list = QListWidget()
        self._raw_blocks_list.currentRowChanged.connect(self._focus_raw_block)
        self._python_blocks_list = QListWidget()
        self._python_blocks_list.currentRowChanged.connect(self._focus_python_block)
        self._raw_move_up = QPushButton()
        self._raw_move_up.clicked.connect(lambda: self._move_raw_block(-1))
        self._raw_move_down = QPushButton()
        self._raw_move_down.clicked.connect(lambda: self._move_raw_block(1))
        self._raw_delete = QPushButton()
        self._raw_delete.clicked.connect(self._delete_raw_block)
        self._python_move_up = QPushButton()
        self._python_move_up.clicked.connect(lambda: self._move_python_block(-1))
        self._python_move_down = QPushButton()
        self._python_move_down.clicked.connect(lambda: self._move_python_block(1))
        self._python_delete = QPushButton()
        self._python_delete.clicked.connect(self._delete_python_block)
        self._editors_tabs.addTab(
            self._build_editor_tab(
                self._raw_editor_label,
                self._raw_blocks_list,
                (self._raw_move_up, self._raw_move_down, self._raw_delete),
                self._raw_editor,
            ),
            "",
        )
        self._editors_tabs.addTab(
            self._build_editor_tab(
                self._python_editor_label,
                self._python_blocks_list,
                (self._python_move_up, self._python_move_down, self._python_delete),
                self._python_editor,
            ),
            "",
        )

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(10)
        editor_layout.addWidget(self._advanced_hint)
        editor_layout.addWidget(self._editors_tabs, 1)
        editor_layout.addWidget(self._status_label)
        editor_actions = QHBoxLayout()
        editor_actions.addWidget(self._apply_button)
        editor_actions.addStretch(1)
        editor_layout.addLayout(editor_actions)

        splitter = configure_splitter(QSplitter())
        splitter.addWidget(template_panel)
        splitter.addWidget(editor_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 900])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.retranslate_ui()
        self._populate_categories()
        self.set_project(None)

    def _build_editor_tab(
        self,
        heading: QLabel,
        block_list: QListWidget,
        action_buttons: tuple[QPushButton, ...],
        editor: QPlainTextEdit,
    ) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(heading)
        layout.addWidget(block_list)
        actions = QHBoxLayout()
        for button in action_buttons:
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addWidget(editor, 1)
        return widget

    def set_project(self, project: Project | None) -> None:
        self._loading = True
        if project is None:
            self._raw_editor.clear()
            self._python_editor.clear()
            self._apply_button.setEnabled(False)
        else:
            self._raw_editor.setPlainText("\n".join(project.advanced_input_overrides))
            self._python_editor.setPlainText(_PYTHON_BLOCK_DELIMITER.join(project.model.python_blocks))
            self._apply_button.setEnabled(True)
        self._loading = False
        self._sync_block_lists()
        self.refresh_validation()

    def refresh_validation(self) -> None:
        self._status_label.setText(
            "\n".join(self._validation_service.messages_for_prefixes("model.scan_trace_count"))
            or self._localization.text("editor.advanced.valid")
        )

    def retranslate_ui(self) -> None:
        self._category_label.setText(self._localization.text("editor.advanced.category"))
        self._insert_template_button.setText(self._localization.text("editor.advanced.insert_template"))
        self._insert_python_button.setText(self._localization.text("editor.advanced.insert_python"))
        self._raw_editor_label.setText(self._localization.text("editor.advanced.raw_commands"))
        self._python_editor_label.setText(self._localization.text("editor.advanced.python_blocks"))
        self._advanced_hint.setText(self._localization.text("editor.advanced.hint"))
        self._apply_button.setText(self._localization.text("editor.advanced.apply"))
        self._raw_move_up.setText(self._localization.text("editor.advanced.move_up"))
        self._raw_move_down.setText(self._localization.text("editor.advanced.move_down"))
        self._raw_delete.setText(self._localization.text("editor.advanced.delete_block"))
        self._python_move_up.setText(self._localization.text("editor.advanced.move_up"))
        self._python_move_down.setText(self._localization.text("editor.advanced.move_down"))
        self._python_delete.setText(self._localization.text("editor.advanced.delete_block"))
        self._editors_tabs.setTabText(0, self._localization.text("editor.advanced.raw_tab"))
        self._editors_tabs.setTabText(1, self._localization.text("editor.advanced.python_tab"))
        self._sync_block_lists()
        self.refresh_validation()

    def _populate_categories(self) -> None:
        current_category = self._category_combo.currentData()
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        self._category_combo.addItem(self._localization.text("editor.advanced.category_all"), "all")
        for category in self._command_registry.categories():
            self._category_combo.addItem(
                self._localization.text(f"editor.advanced.category.{category}"),
                category,
            )
        self._category_combo.blockSignals(False)
        index = self._category_combo.findData(current_category)
        self._category_combo.setCurrentIndex(index if index >= 0 else 0)
        self._populate_templates()

    def _populate_templates(self) -> None:
        current_key = self._current_template_key()
        category = str(self._category_combo.currentData() or "all")
        self._template_list.clear()
        for template in self._command_registry.templates(category):
            item = QListWidgetItem(template.title)
            item.setData(256, template.key)
            self._template_list.addItem(item)
        if self._template_list.count():
            target_index = 0
            for index in range(self._template_list.count()):
                if self._template_list.item(index).data(256) == current_key:
                    target_index = index
                    break
            self._template_list.setCurrentRow(target_index)
        else:
            self._template_description.clear()

    def _current_template_key(self) -> str | None:
        item = self._template_list.currentItem()
        if item is None:
            return None
        return str(item.data(256))

    def _update_template_preview(self) -> None:
        template = self._selected_template()
        if template is None:
            self._template_description.clear()
            return
        self._template_description.setText(
            f"{template.description}\n\n{template.template}"
        )

    def _selected_template(self):
        key = self._current_template_key()
        if key is None:
            return None
        return self._command_registry.get(key)

    def _insert_template(self) -> None:
        template = self._selected_template()
        if template is None:
            return
        cursor = self._raw_editor.textCursor()
        insertion = template.template
        if cursor.position() > 0:
            insertion = "\n" + insertion
        cursor.insertText(insertion)
        self._editors_tabs.setCurrentIndex(0)
        self._sync_block_lists()

    def _insert_python_block(self) -> None:
        cursor = self._python_editor.textCursor()
        insertion = "from user_libs.antennas.GSSI import antenna_like_GSSI_1500\nantenna_like_GSSI_1500(0.125, 0.094, 0.1, resolution=0.002)"
        if cursor.position() > 0 and not self._python_editor.toPlainText().endswith(_PYTHON_BLOCK_DELIMITER):
            insertion = _PYTHON_BLOCK_DELIMITER + insertion
        cursor.insertText(insertion)
        self._editors_tabs.setCurrentIndex(1)
        self._sync_block_lists()

    def _apply_changes(self) -> None:
        if self._loading:
            return
        self._model_editor_service.update_advanced_workspace(
            python_blocks=self._split_python_blocks(self._python_editor.toPlainText()),
            raw_input_overrides=self._split_raw_commands(self._raw_editor.toPlainText()),
        )
        self.refresh_validation()
        self.model_changed.emit()

    def _split_python_blocks(self, text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []
        return [item.strip() for item in normalized.split(_PYTHON_BLOCK_DELIMITER) if item.strip()]

    def _split_raw_commands(self, text: str) -> list[str]:
        return [line.rstrip() for line in text.splitlines() if line.strip()]

    def _sync_block_lists(self) -> None:
        if self._loading:
            return
        raw_selection = self._raw_blocks_list.currentRow()
        python_selection = self._python_blocks_list.currentRow()
        raw_blocks = self._split_raw_commands(self._raw_editor.toPlainText())
        python_blocks = self._split_python_blocks(self._python_editor.toPlainText())

        self._raw_blocks_list.blockSignals(True)
        self._raw_blocks_list.clear()
        for index, block in enumerate(raw_blocks, start=1):
            self._raw_blocks_list.addItem(f"{index}. {block}")
        self._raw_blocks_list.blockSignals(False)

        self._python_blocks_list.blockSignals(True)
        self._python_blocks_list.clear()
        for index, block in enumerate(python_blocks, start=1):
            first_line = block.splitlines()[0] if block.splitlines() else "Python block"
            self._python_blocks_list.addItem(f"{index}. {first_line}")
        self._python_blocks_list.blockSignals(False)

        if self._raw_blocks_list.count():
            self._raw_blocks_list.setCurrentRow(min(max(raw_selection, 0), self._raw_blocks_list.count() - 1))
        if self._python_blocks_list.count():
            self._python_blocks_list.setCurrentRow(min(max(python_selection, 0), self._python_blocks_list.count() - 1))

    def _focus_raw_block(self, row: int) -> None:
        if row < 0:
            return
        blocks = self._split_raw_commands(self._raw_editor.toPlainText())
        if row >= len(blocks):
            return
        cursor = self._raw_editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for index, line in enumerate(blocks):
            if index == row:
                break
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        self._raw_editor.setTextCursor(cursor)
        self._raw_editor.setFocus(Qt.FocusReason.OtherFocusReason)

    def _focus_python_block(self, row: int) -> None:
        if row < 0:
            return
        blocks = self._split_python_blocks(self._python_editor.toPlainText())
        if row >= len(blocks):
            return
        cursor = self._python_editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for index in range(row):
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        self._python_editor.setTextCursor(cursor)
        self._python_editor.setFocus(Qt.FocusReason.OtherFocusReason)

    def _move_raw_block(self, direction: int) -> None:
        row = self._raw_blocks_list.currentRow()
        blocks = self._split_raw_commands(self._raw_editor.toPlainText())
        target = row + direction
        if row < 0 or target < 0 or target >= len(blocks):
            return
        blocks[row], blocks[target] = blocks[target], blocks[row]
        self._loading = True
        self._raw_editor.setPlainText("\n".join(blocks))
        self._loading = False
        self._sync_block_lists()
        self._raw_blocks_list.setCurrentRow(target)

    def _delete_raw_block(self) -> None:
        row = self._raw_blocks_list.currentRow()
        blocks = self._split_raw_commands(self._raw_editor.toPlainText())
        if row < 0 or row >= len(blocks):
            return
        del blocks[row]
        self._loading = True
        self._raw_editor.setPlainText("\n".join(blocks))
        self._loading = False
        self._sync_block_lists()

    def _move_python_block(self, direction: int) -> None:
        row = self._python_blocks_list.currentRow()
        blocks = self._split_python_blocks(self._python_editor.toPlainText())
        target = row + direction
        if row < 0 or target < 0 or target >= len(blocks):
            return
        blocks[row], blocks[target] = blocks[target], blocks[row]
        self._loading = True
        self._python_editor.setPlainText(_PYTHON_BLOCK_DELIMITER.join(blocks))
        self._loading = False
        self._sync_block_lists()
        self._python_blocks_list.setCurrentRow(target)

    def _delete_python_block(self) -> None:
        row = self._python_blocks_list.currentRow()
        blocks = self._split_python_blocks(self._python_editor.toPlainText())
        if row < 0 or row >= len(blocks):
            return
        del blocks[row]
        self._loading = True
        self._python_editor.setPlainText(_PYTHON_BLOCK_DELIMITER.join(blocks))
        self._loading = False
        self._sync_block_lists()
