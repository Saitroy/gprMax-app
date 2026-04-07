from __future__ import annotations

from PySide6.QtWidgets import QApplication


STYLESHEET = """
QWidget {
    background-color: #eef3f6;
    color: #243240;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}
QMainWindow {
    background: #e8eef3;
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
QListWidget#ContextNavigation {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget#ContextNavigation::item {
    border-radius: 10px;
    margin: 2px 0;
    padding: 10px 12px;
    color: #324352;
}
QListWidget#ContextNavigation::item:selected {
    background: #dce6ef;
    color: #21313f;
    border: 1px solid #c5d2dd;
}
QListWidget#ContextNavigation::item:hover:!selected {
    background: #eef3f7;
}
QFrame#ViewCard {
    background: #fbfcfd;
    border: 1px solid #d6dee6;
    border-radius: 18px;
}
QFrame#AppHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #213343, stop:1 #31485d);
    border: 1px solid #415a71;
    border-radius: 20px;
}
QLabel#HeaderTitle {
    background: transparent;
    color: #f3f7fa;
    font-family: "Bahnschrift SemiCondensed";
    font-size: 20pt;
    font-weight: 700;
}
QLabel#HeaderSubtitle {
    background: transparent;
    color: #b8c7d4;
    font-size: 9.6pt;
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
QLabel#PanelTitle {
    font-family: "Bahnschrift SemiCondensed";
    font-size: 16pt;
    font-weight: 700;
}
QLabel#SectionTitle {
    font-size: 11pt;
    font-weight: 600;
}
QLabel#SubsectionTitle {
    color: #475a6b;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
QLabel#SectionBody {
    color: #62717f;
    line-height: 1.3em;
}
QPushButton {
    background: #f8fbfd;
    color: #23313f;
    border: 1px solid #c8d3dc;
    border-radius: 11px;
    padding: 8px 14px;
    font-weight: 600;
    min-height: 18px;
}
QPushButton:hover {
    background: #edf4f8;
    border-color: #91a5b8;
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
QPushButton#HeaderPrimaryButton {
    background: #dbe8f3;
    color: #1e3243;
    border: 1px solid #bfd1e0;
    border-radius: 12px;
    padding: 9px 16px;
}
QPushButton#HeaderPrimaryButton:hover {
    background: #e8f1f7;
    border-color: #d2e0ec;
}
QPushButton#HeaderPrimaryButton:pressed {
    background: #cfdeea;
}
QPushButton#PrimaryButton:hover {
    background: #5c778c;
    border-color: #4d6679;
}
QPushButton#PrimaryButton:pressed {
    background: #526a7e;
}
QToolButton#InfoButton {
    background: rgba(255, 255, 255, 0.16);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.32);
    border-radius: 15px;
    font-size: 10pt;
    font-weight: 700;
    min-width: 30px;
    min-height: 30px;
    padding: 0px;
}
QToolButton#InfoButton:hover {
    background: rgba(255, 255, 255, 0.22);
    border-color: rgba(255, 255, 255, 0.44);
}
QToolButton#InfoButton:pressed {
    background: rgba(255, 255, 255, 0.28);
}
QLineEdit,
QPlainTextEdit,
QListWidget,
QTreeWidget,
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
QTreeWidget:focus,
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
QTreeWidget#ProjectExplorer {
    background: transparent;
    border: none;
    outline: none;
}
QTreeWidget#ProjectExplorer::item {
    border-radius: 10px;
    padding: 8px 10px;
    margin: 2px 0;
}
QTreeWidget#ProjectExplorer::item:selected {
    background: #d8e7f1;
    color: #1f3344;
}
QTreeWidget#ProjectExplorer::item:hover:!selected {
    background: #edf4f8;
}
QSplitter::handle {
    background: transparent;
}
QSplitter::handle:horizontal {
    width: 10px;
    margin: 0 2px;
    border-left: 1px solid #c7d2db;
    border-right: 1px solid #f6f9fb;
    background: rgba(231, 238, 243, 0.68);
}
QSplitter::handle:vertical {
    height: 10px;
    margin: 2px 0;
    border-top: 1px solid #c7d2db;
    border-bottom: 1px solid #f6f9fb;
    background: rgba(231, 238, 243, 0.68);
}
QSplitter::handle:hover:horizontal,
QSplitter::handle:pressed:horizontal {
    border-left-color: #70879b;
    background: rgba(214, 226, 235, 0.95);
}
QSplitter::handle:hover:vertical,
QSplitter::handle:pressed:vertical {
    border-top-color: #70879b;
    background: rgba(214, 226, 235, 0.95);
}
QFrame#WorkbenchSidebar {
    background: #fbfcfd;
    border: 1px solid #d6dee6;
    border-radius: 18px;
}
QTabWidget::pane {
    background: #fbfbfa;
    border: 1px solid #d7dee4;
    border-radius: 14px;
    top: -1px;
}
QTabWidget#WorkbenchTabs::pane,
QTabWidget#DetailTabs::pane {
    background: #fbfcfd;
    border: 1px solid #d6dee6;
    border-radius: 16px;
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
QLabel#StatusPill {
    background: #e3edf4;
    color: #214058;
    border: 1px solid #c6d6e2;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 700;
}
QLabel#StatusDetail {
    color: #546677;
    padding: 0 4px;
}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(STYLESHEET)
