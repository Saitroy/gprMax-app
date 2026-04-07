from __future__ import annotations

from PySide6.QtWidgets import QSplitter


def configure_splitter(
    splitter: QSplitter,
    *,
    handle_width: int = 10,
    children_collapsible: bool = False,
) -> QSplitter:
    splitter.setObjectName("WorkbenchSplitter")
    splitter.setHandleWidth(handle_width)
    splitter.setChildrenCollapsible(children_collapsible)
    splitter.setOpaqueResize(True)
    return splitter
