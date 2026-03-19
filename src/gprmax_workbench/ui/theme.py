from __future__ import annotations

from PySide6.QtWidgets import QApplication


STYLESHEET = """
QWidget {
    background-color: #f2f4f3;
    color: #243240;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}
QMainWindow {
    background: #f2f4f3;
}
QScrollArea#PageScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #d6dde4;
    width: 16px;
    margin: 6px 4px 6px 2px;
    border-radius: 8px;
}
QScrollBar::handle:vertical {
    background: #698197;
    min-height: 56px;
    border-radius: 8px;
    border: 1px solid #5a7288;
}
QScrollBar::handle:vertical:hover {
    background: #5d7489;
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
    background: #d6dde4;
    height: 14px;
    margin: 2px 6px 4px 6px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal {
    background: #698197;
    min-width: 48px;
    border-radius: 7px;
    border: 1px solid #5a7288;
}
QScrollBar::handle:horizontal:hover {
    background: #5d7489;
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
    background: #f2f4f3;
    color: #314250;
    border-bottom: 1px solid #d8dee4;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 8px;
}
QMenuBar::item:selected {
    background: #dce5ec;
}
QMenu {
    background: #fbfbfa;
    color: #243240;
    border: 1px solid #d2d8de;
    padding: 6px;
}
QMenu::item {
    padding: 8px 12px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: #dce5ec;
}
QFrame#Sidebar {
    background-color: #2d3f50;
    border-radius: 18px;
    border: 1px solid #3f556a;
}
QLabel#AppTitle {
    background-color: #2d3f50;
    color: #f6fafc;
    font-family: "Bahnschrift SemiCondensed";
    font-size: 20pt;
    font-weight: 700;
}
QLabel#AppSubtitle {
    background-color: #2d3f50;
    color: #d5dee6;
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
    background: #fbfbfa;
    border: 1px solid #d7dee4;
    border-radius: 18px;
}
QFrame#WorkspaceBanner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8fbfc, stop:1 #ecf2f6);
    border: 1px solid #d6dee5;
    border-radius: 20px;
}
QFrame#HeroCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2f4355, stop:1 #415b72);
    border: 1px solid #516a81;
    border-radius: 20px;
}
QFrame#MetricTile {
    background: #f7fafb;
    border: 1px solid #d5dee5;
    border-radius: 16px;
    min-width: 138px;
}
QLabel#BannerEyebrow,
QLabel#HeroEyebrow,
QLabel#MetricEyebrow {
    color: #6b7c8d;
    font-size: 8.8pt;
    font-weight: 600;
}
QLabel#HeroEyebrow {
    color: #bed0de;
    background: transparent;
}
QLabel#BannerTitle,
QLabel#HeroTitle,
QLabel#MetricValue {
    font-family: "Bahnschrift SemiCondensed";
    color: #23313f;
    font-weight: 700;
    background: transparent;
}
QLabel#BannerTitle {
    font-size: 18pt;
}
QLabel#HeroTitle {
    color: #ffffff;
    font-size: 21pt;
}
QLabel#HeroBody,
QLabel#BannerSubtitle,
QLabel#BannerMeta,
QLabel#MetricCaption {
    color: #5d6f80;
    background: transparent;
}
QLabel#HeroBody {
    color: #dbe6ee;
}
QLabel#MetricValue {
    font-size: 14pt;
}
QLabel#MetricCaption {
    font-size: 9pt;
}
QLabel#ViewTitle {
    font-family: "Bahnschrift SemiCondensed";
    font-size: 22pt;
    font-weight: 700;
}
QLabel#ViewSubtitle {
    color: #617180;
    font-size: 10pt;
}
QLabel#SectionTitle {
    font-size: 11pt;
    font-weight: 600;
}
QLabel#SectionBody {
    color: #62717f;
    line-height: 1.3em;
}
QPushButton {
    background: #f7fafc;
    color: #23313f;
    border: 1px solid #90a4b8;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 600;
    min-height: 18px;
}
QPushButton:hover {
    background: #eef3f7;
    border-color: #758ba0;
}
QPushButton:pressed {
    background: #e1e8ee;
    border-color: #607688;
}
QPushButton:disabled {
    background: #f0f3f5;
    color: #8b98a5;
    border-color: #c7d1da;
}
QPushButton#PrimaryButton {
    background: #668298;
    color: #ffffff;
    border: 1px solid #557085;
}
QPushButton#PrimaryButton:hover {
    background: #5c778c;
    border-color: #4d6679;
}
QPushButton#PrimaryButton:pressed {
    background: #526a7e;
}
QLineEdit,
QPlainTextEdit,
QListWidget,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    background: #ffffff;
    color: #23313f;
    border: 1px solid #c8d2db;
    border-radius: 10px;
    padding: 6px 8px;
    selection-background-color: #d6e3ec;
    selection-color: #23313f;
}
QLineEdit:focus,
QPlainTextEdit:focus,
QListWidget:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border-color: #7e96ab;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QAbstractItemView {
    background: #ffffff;
    color: #23313f;
    border: 1px solid #c8d2db;
    selection-background-color: #dce6ef;
    selection-color: #23313f;
}
QSplitter::handle {
    background: transparent;
}
QSplitter::handle:hover {
    background: #d9e2e9;
}
QTabWidget::pane {
    background: #fbfbfa;
    border: 1px solid #d7dee4;
    border-radius: 14px;
    top: -1px;
}
QTabBar::tab {
    background: #e6edf2;
    color: #415361;
    border: 1px solid #d7dee4;
    border-bottom: none;
    padding: 8px 14px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QTabBar::tab:selected {
    background: #fbfbfa;
    color: #23313f;
}
QGroupBox {
    background: #f7fafb;
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
    background: #668298;
    border-color: #557085;
}
QStatusBar {
    background: #f8fafc;
    border-top: 1px solid #d4dde6;
}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(STYLESHEET)
