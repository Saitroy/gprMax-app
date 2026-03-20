from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class GprMaxHighlighter(QSyntaxHighlighter):
    """Minimal syntax highlighting for gprMax command editors."""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._command_format = QTextCharFormat()
        self._command_format.setForeground(QColor("#1f5f8b"))
        self._command_format.setFontWeight(QFont.Weight.Bold)

        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(QColor("#64748b"))
        self._comment_format.setFontItalic(True)

        self._python_format = QTextCharFormat()
        self._python_format.setForeground(QColor("#0f766e"))

    def highlightBlock(self, text: str) -> None:
        stripped = text.lstrip()
        if stripped.startswith("#") and ":" in stripped:
            self.setFormat(0, len(text), self._command_format)
            return
        if stripped.startswith("#"):
            self.setFormat(0, len(text), self._comment_format)
            return
        if stripped.startswith("from ") or stripped.startswith("import "):
            self.setFormat(0, len(text), self._python_format)
            return
        if stripped.startswith("def ") or stripped.startswith("for ") or stripped.startswith("if "):
            self.setFormat(0, len(text), self._python_format)
            return
        if "resolution=" in text or "rotate90=" in text:
            self.setFormat(0, len(text), self._python_format)
