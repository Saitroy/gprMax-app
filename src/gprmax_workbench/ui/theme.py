from __future__ import annotations

from PySide6.QtWidgets import QApplication


STYLESHEET = """
QWidget {
    background-color: #edf2f6;
    color: #23313f;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}
QMainWindow {
    background: #edf2f6;
}
QScrollArea#PageScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #dbe4ec;
    width: 16px;
    margin: 6px 4px 6px 2px;
    border-radius: 8px;
}
QScrollBar::handle:vertical {
    background: #6f879d;
    min-height: 56px;
    border-radius: 8px;
    border: 1px solid #5d7489;
}
QScrollBar::handle:vertical:hover {
    background: #61798f;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    background: transparent;
    border: none;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: #dbe4ec;
    height: 14px;
    margin: 2px 6px 4px 6px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal {
    background: #6f879d;
    min-width: 48px;
    border-radius: 7px;
    border: 1px solid #5d7489;
}
QScrollBar::handle:horizontal:hover {
    background: #61798f;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
    background: transparent;
    border: none;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}
QMenuBar {
    background: #edf2f6;
    color: #314250;
    border-bottom: 1px solid #d4dde6;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 8px;
}
QMenuBar::item:selected {
    background: #dce6ef;
}
QMenu {
    background: #fbfcfd;
    color: #23313f;
    border: 1px solid #cfd9e2;
    padding: 6px;
}
QMenu::item {
    padding: 8px 12px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: #dce6ef;
}
QFrame#Sidebar {
    background-color: #33475b;
    border-radius: 18px;
    border: 1px solid #41586d;
}
QLabel#AppTitle {
    background-color: #33475b;
    color: #f8fbfd;
    font-size: 19pt;
    font-weight: 700;
}
QLabel#AppSubtitle {
    background-color: #33475b;
    color: #d7e1ea;
    font-size: 9.5pt;
}
QListWidget#Navigation {
    background: transparent;
    border: none;
    color: #eef4f7;
    outline: none;
}
QListWidget#Navigation::item {
    border-radius: 12px;
    margin: 3px 0;
    padding: 10px 12px;
}
QListWidget#Navigation::item:selected {
    background: #d7e4ef;
    color: #223341;
}
QListWidget#Navigation::item:hover:!selected {
    background: rgba(255, 255, 255, 0.12);
}
QFrame#ViewCard {
    background: #fbfcfd;
    border: 1px solid #d4dde6;
    border-radius: 18px;
}
QLabel#ViewTitle {
    font-size: 20pt;
    font-weight: 700;
}
QLabel#ViewSubtitle {
    color: #5b6b7b;
    font-size: 10pt;
}
QLabel#SectionTitle {
    font-size: 11pt;
    font-weight: 600;
}
QLabel#SectionBody {
    color: #5b6b7b;
    line-height: 1.3em;
}
QPushButton {
    background: #f7fafc;
    color: #23313f;
    border: 1px solid #9fb1c2;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 600;
    min-height: 18px;
}
QPushButton:hover {
    background: #eef4f8;
    border-color: #8397ab;
}
QPushButton:pressed {
    background: #e3ebf2;
    border-color: #6f8398;
}
QPushButton:disabled {
    background: #f2f5f7;
    color: #8b98a5;
    border-color: #c7d1da;
}
QPushButton#PrimaryButton {
    background: #6a869f;
    color: #ffffff;
    border: 1px solid #587289;
}
QPushButton#PrimaryButton:hover {
    background: #5e7991;
    border-color: #4d667c;
}
QPushButton#PrimaryButton:pressed {
    background: #526b81;
}
QLineEdit,
QPlainTextEdit,
QListWidget,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    background: #ffffff;
    color: #23313f;
    border: 1px solid #c6d1db;
    border-radius: 10px;
    padding: 6px 8px;
    selection-background-color: #d7e4ef;
    selection-color: #23313f;
}
QLineEdit:focus,
QPlainTextEdit:focus,
QListWidget:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border-color: #7d95ab;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QAbstractItemView {
    background: #ffffff;
    color: #23313f;
    border: 1px solid #c6d1db;
    selection-background-color: #dce6ef;
    selection-color: #23313f;
}
QTabWidget::pane {
    background: #fbfcfd;
    border: 1px solid #d4dde6;
    border-radius: 14px;
    top: -1px;
}
QTabBar::tab {
    background: #e8eef3;
    color: #405160;
    border: 1px solid #d4dde6;
    border-bottom: none;
    padding: 8px 14px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QTabBar::tab:selected {
    background: #fbfcfd;
    color: #23313f;
}
QGroupBox {
    background: #f7fafc;
    border: 1px solid #d8e0e7;
    border-radius: 14px;
    margin-top: 10px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QCheckBox {
    color: #23313f;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #9fb1c2;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #6a869f;
    border-color: #587289;
}
QStatusBar {
    background: #f8fafc;
    border-top: 1px solid #d4dde6;
}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(STYLESHEET)
