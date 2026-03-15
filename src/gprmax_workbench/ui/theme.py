from __future__ import annotations

from PySide6.QtWidgets import QApplication


STYLESHEET = """
QWidget {
    background-color: #f4f1ea;
    color: #1f2933;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}
QMainWindow {
    background: #f4f1ea;
}
QFrame#Sidebar {
    background-color: #1f2933;
    border-radius: 18px;
}
QLabel#AppTitle {
    color: #fdf6e3;
    font-size: 19pt;
    font-weight: 700;
}
QLabel#AppSubtitle {
    color: #cdd6dd;
    font-size: 9.5pt;
}
QListWidget#Navigation {
    background: transparent;
    border: none;
    color: #e6edf1;
    outline: none;
}
QListWidget#Navigation::item {
    border-radius: 12px;
    margin: 3px 0;
    padding: 10px 12px;
}
QListWidget#Navigation::item:selected {
    background: #d97706;
    color: #fff9f0;
}
QListWidget#Navigation::item:hover:!selected {
    background: rgba(244, 241, 234, 0.12);
}
QFrame#ViewCard {
    background: #fffaf2;
    border: 1px solid #e5dccd;
    border-radius: 18px;
}
QLabel#ViewTitle {
    font-size: 20pt;
    font-weight: 700;
}
QLabel#ViewSubtitle {
    color: #52606d;
    font-size: 10pt;
}
QLabel#SectionTitle {
    font-size: 11pt;
    font-weight: 600;
}
QLabel#SectionBody {
    color: #52606d;
    line-height: 1.3em;
}
QStatusBar {
    background: #fffaf2;
    border-top: 1px solid #e5dccd;
}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(STYLESHEET)
