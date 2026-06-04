from __future__ import annotations

from PySide6.QtWidgets import QApplication


COLORS = {
    "app_bg": "#f6f8fb",
    "surface": "#ffffff",
    "surface_alt": "#f9fafb",
    "surface_muted": "#f1f5f9",
    "border": "#e2e8f0",
    "border_strong": "#cbd5e1",
    "text": "#111827",
    "text_muted": "#64748b",
    "text_soft": "#94a3b8",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "primary_pressed": "#1e40af",
    "primary_soft": "#e8f1ff",
    "success": "#16a34a",
    "success_soft": "#eaf7ee",
    "warning": "#d97706",
    "warning_soft": "#fff7e6",
    "error": "#dc2626",
    "error_soft": "#feecec",
    "info": "#0284c7",
    "info_soft": "#e8f6fd",
}

RADIUS = {
    "sm": 5,
    "md": 8,
    "lg": 10,
}

SPACING = {
    "button_v": 7,
    "button_h": 13,
    "field_v": 6,
    "field_h": 8,
}


def _build_stylesheet() -> str:
    c = COLORS
    r = RADIUS
    s = SPACING
    return f"""
QWidget {{
    background-color: {c["app_bg"]};
    color: {c["text"]};
    font-family: "Segoe UI";
    font-size: 10pt;
}}
QMainWindow {{
    background: {c["app_bg"]};
}}
QDialog {{
    background: {c["surface"]};
}}
QLabel {{
    background: transparent;
}}
QToolTip {{
    background: #0f172a;
    color: #ffffff;
    border: 1px solid #334155;
    border-radius: {r["md"]}px;
    padding: 7px 9px;
}}
QScrollArea#PageScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 6px 2px 6px 2px;
}}
QScrollBar::handle:vertical {{
    background: #cbd5e1;
    min-height: 48px;
    border-radius: 6px;
}}
QScrollBar::handle:vertical:hover {{
    background: #94a3b8;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
    background: transparent;
    border: none;
}}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 12px;
    margin: 2px 6px 2px 6px;
}}
QScrollBar::handle:horizontal {{
    background: #cbd5e1;
    min-width: 48px;
    border-radius: 6px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #94a3b8;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
    background: transparent;
    border: none;
}}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
}}
QMenuBar {{
    background: {c["surface"]};
    color: {c["text"]};
    border-bottom: 1px solid {c["border"]};
}}
QMenuBar::item {{
    background: transparent;
    padding: 6px 10px;
    border-radius: {r["md"]}px;
}}
QMenuBar::item:selected {{
    background: {c["surface_muted"]};
}}
QMenu {{
    background: {c["surface"]};
    color: {c["text"]};
    border: 1px solid {c["border"]};
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 12px;
    border-radius: {r["md"]}px;
}}
QMenu::item:selected {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
}}
QFrame#Sidebar {{
    background-color: {c["surface_alt"]};
    border-radius: {r["lg"]}px;
    border: 1px solid {c["border"]};
}}
QLabel#AppTitle {{
    background: {c["primary"]};
    color: #ffffff;
    border-radius: 18px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
    font-family: "Segoe UI";
    font-size: 16pt;
    font-weight: 700;
}}
QLabel#AppSubtitle {{
    background: transparent;
    color: {c["text_muted"]};
    font-size: 9pt;
}}
QFrame#SidebarStatus {{
    background: {c["surface_alt"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
}}
QFrame#ActionBar {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
}}
QLabel#SidebarSectionTitle {{
    background: transparent;
    color: {c["text_muted"]};
    font-size: 8.8pt;
    font-weight: 700;
    text-transform: uppercase;
}}
QPushButton[buttonRole="sidebar"] {{
    background: {c["surface"]};
    color: {c["text"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    padding: 7px 10px;
    text-align: left;
}}
QPushButton[buttonRole="sidebar"]:hover {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
    border-color: #bfdbfe;
}}
QPushButton[buttonRole="sidebar"]:pressed {{
    background: #dbeafe;
    border-color: #93c5fd;
}}
QPushButton[buttonRole="rail"] {{
    background: {c["surface"]};
    color: {c["text_muted"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    min-height: 34px;
    max-height: 34px;
    padding: 0;
    font-size: 8pt;
    font-weight: 700;
}}
QPushButton[buttonRole="rail"]:hover {{
    background: #e0ecff;
    color: {c["primary_pressed"]};
    border-color: #bfdbfe;
}}
QPushButton[buttonRole="rail"]:pressed {{
    background: {c["primary"]};
    color: #ffffff;
    border-color: {c["primary"]};
}}
QListWidget#Navigation {{
    background: transparent;
    border: none;
    color: {c["text_muted"]};
    outline: none;
}}
QListWidget#Navigation::item {{
    border: 1px solid transparent;
    border-radius: {r["md"]}px;
    margin: 2px 0;
    padding: 0;
}}
QListWidget#Navigation::item:selected {{
    background: {c["primary"]};
    color: #ffffff;
    border-color: {c["primary"]};
}}
QListWidget#Navigation::item:hover:!selected {{
    background: #e0ecff;
    color: {c["primary_pressed"]};
    border-color: #bfdbfe;
}}
QListWidget#ContextNavigation {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget#ContextNavigation::item {{
    border-radius: {r["md"]}px;
    margin: 2px 0;
    padding: 9px 10px;
    color: {c["text_muted"]};
}}
QListWidget#ContextNavigation::item:selected {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
    border: 1px solid #bfdbfe;
}}
QListWidget#ContextNavigation::item:hover:!selected {{
    background: {c["surface_muted"]};
    color: {c["text"]};
}}
QFrame#ViewCard,
QFrame#ModelOverviewCard,
QFrame#ValidationSummaryCard,
QFrame#WorkbenchSidebar,
QFrame#WorkbenchLayerRail {{
    background: {c["surface"]};
    border: 1px solid #e5edf5;
    border-radius: {r["md"]}px;
}}
QFrame#ModelOverviewCard {{
    border-color: {c["border"]};
}}
QFrame#ValidationSummaryCard {{
    background: {c["surface"]};
}}
QFrame[scenePanelRole="guide"],
QFrame[scenePanelRole="domain"],
QFrame[scenePanelRole="palette"],
QFrame[scenePanelRole="inspector"],
QFrame[scenePanelRole="entities"] {{
    background: {c["surface"]};
    border-color: #e5edf5;
}}
QFrame#AppHeader {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: {r["lg"]}px;
}}
QLabel#HeaderTitle {{
    background: transparent;
    color: {c["text"]};
    font-family: "Segoe UI";
    font-size: 18pt;
    font-weight: 700;
}}
QLabel#HeaderSubtitle {{
    background: transparent;
    color: {c["text_muted"]};
    font-size: 9.4pt;
}}
QFrame#WorkspaceBanner {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
}}
QFrame#HeroCard {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
}}
QFrame#MetricTile {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    min-width: 134px;
}}
QLabel#BannerEyebrow,
QLabel#HeroEyebrow,
QLabel#MetricEyebrow {{
    color: {c["primary"]};
    font-size: 8.6pt;
    font-weight: 700;
}}
QLabel#BannerTitle,
QLabel#HeroTitle,
QLabel#MetricValue {{
    font-family: "Segoe UI";
    color: {c["text"]};
    font-weight: 700;
    background: transparent;
}}
QLabel#BannerTitle {{
    font-size: 17pt;
}}
QLabel#HeroTitle {{
    font-size: 18pt;
}}
QLabel#HeroBody,
QLabel#BannerSubtitle,
QLabel#BannerMeta,
QLabel#MetricCaption {{
    color: {c["text_muted"]};
    background: transparent;
}}
QLabel#MetricValue {{
    font-size: 13pt;
}}
QLabel#MetricCaption {{
    font-size: 8.8pt;
}}
QLabel#ModelOverviewCounts {{
    color: {c["text"]};
    background: {c["surface_alt"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    padding: 8px 10px;
    font-size: 9pt;
}}
QLabel#ModelNextAction {{
    color: #1e3a8a;
    background: {c["primary_soft"]};
    border: 1px solid #bfdbfe;
    border-radius: {r["md"]}px;
    padding: 8px 10px;
    font-weight: 600;
}}
QLabel#ValidationIssueText {{
    color: {c["text_muted"]};
    background: transparent;
}}
QLabel#TechnicalDetails {{
    color: {c["text_muted"]};
    background: {c["surface_alt"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    padding: 8px 10px;
    font-family: "Consolas";
    font-size: 8.8pt;
}}
QLabel#ViewTitle {{
    font-family: "Segoe UI";
    font-size: 20pt;
    font-weight: 700;
    color: {c["text"]};
}}
QLabel#ViewSubtitle {{
    color: {c["text_muted"]};
    font-size: 9.8pt;
}}
QLabel#PanelTitle {{
    font-family: "Segoe UI";
    font-size: 14pt;
    font-weight: 700;
    color: {c["text"]};
}}
QLabel#SectionTitle {{
    font-size: 10.5pt;
    font-weight: 700;
    color: {c["text"]};
}}
QLabel#SubsectionTitle {{
    color: {c["text_muted"]};
    font-size: 8.8pt;
    font-weight: 700;
    text-transform: uppercase;
}}
QLabel#SectionBody {{
    color: {c["text_muted"]};
    line-height: 1.3em;
}}
QPushButton {{
    background: {c["surface"]};
    color: {c["text"]};
    border: 1px solid {c["border_strong"]};
    border-radius: {r["md"]}px;
    padding: {s["button_v"]}px {s["button_h"]}px;
    font-weight: 600;
    min-height: 18px;
}}
QPushButton:hover {{
    background: {c["surface_muted"]};
    border-color: #94a3b8;
}}
QPushButton:pressed {{
    background: #e2e8f0;
    border-color: #94a3b8;
}}
QPushButton:disabled {{
    background: #f1f5f9;
    color: {c["text_soft"]};
    border-color: {c["border"]};
}}
QPushButton#PrimaryButton,
QPushButton[buttonRole="primary"] {{
    background: {c["primary"]};
    color: #ffffff;
    border: 1px solid {c["primary"]};
}}
QPushButton#PrimaryButton:hover,
QPushButton[buttonRole="primary"]:hover {{
    background: {c["primary_hover"]};
    border-color: {c["primary_hover"]};
}}
QPushButton#PrimaryButton:pressed,
QPushButton[buttonRole="primary"]:pressed {{
    background: {c["primary_pressed"]};
    border-color: {c["primary_pressed"]};
}}
QPushButton#PrimaryButton:disabled,
QPushButton[buttonRole="primary"]:disabled {{
    background: #bfdbfe;
    color: #eff6ff;
    border-color: #bfdbfe;
}}
QPushButton#HeaderPrimaryButton,
QPushButton[buttonRole="secondary"] {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
    border: 1px solid #bfdbfe;
}}
QPushButton#HeaderPrimaryButton:hover,
QPushButton[buttonRole="secondary"]:hover {{
    background: #dbeafe;
    border-color: #93c5fd;
}}
QPushButton#HeaderPrimaryButton:pressed,
QPushButton[buttonRole="secondary"]:pressed {{
    background: #bfdbfe;
}}
QPushButton[buttonRole="ghost"] {{
    background: transparent;
    color: {c["primary"]};
    border: 1px solid transparent;
}}
QPushButton[buttonRole="ghost"]:hover {{
    background: {c["primary_soft"]};
    border-color: #dbeafe;
}}
QPushButton[buttonRole="ghost"]:pressed {{
    background: #dbeafe;
}}
QPushButton[buttonRole="projectCard"] {{
    background: {c["surface"]};
    color: {c["text"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    padding: 10px 12px;
    text-align: left;
    min-height: 34px;
}}
QPushButton[buttonRole="projectCard"]:hover {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
    border-color: #bfdbfe;
}}
QPushButton[buttonRole="projectCard"]:pressed {{
    background: #dbeafe;
    border-color: #93c5fd;
}}
QPushButton[buttonRole="destructive"] {{
    background: {c["error_soft"]};
    color: #991b1b;
    border: 1px solid #fecaca;
}}
QPushButton[buttonRole="destructive"]:hover {{
    background: #fee2e2;
    border-color: #fca5a5;
}}
QPushButton[buttonRole="destructive"]:pressed {{
    background: #fecaca;
}}
QPushButton[sectionButton="true"] {{
    background: {c["surface_alt"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    color: {c["text_muted"]};
    padding: 8px 12px;
    font-weight: 600;
}}
QPushButton[sectionButton="true"]:hover {{
    background: {c["surface_muted"]};
    border-color: {c["border_strong"]};
    color: {c["text"]};
}}
QPushButton[sectionButton="true"]:checked {{
    background: {c["primary_soft"]};
    border-color: #93c5fd;
    color: {c["primary_pressed"]};
}}
QPushButton[sectionButton="true"][sectionStatus="complete"] {{
    border-color: #bbf7d0;
    color: #166534;
}}
QPushButton[sectionButton="true"][sectionStatus="warning"] {{
    border-color: #fed7aa;
    color: #92400e;
}}
QPushButton[sectionButton="true"][sectionStatus="error"] {{
    border-color: #fecaca;
    color: #991b1b;
}}
QPushButton[sectionButton="true"][sectionStatus="empty"] {{
    color: {c["text_soft"]};
}}
QPushButton[sectionButton="true"][sectionStatus="advanced"] {{
    border-color: #c4b5fd;
    color: #5b21b6;
    background: #f5f3ff;
}}
QPushButton[buttonRole="validationIssue"] {{
    background: {c["surface"]};
    color: {c["text"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    padding: 8px 10px;
    text-align: left;
}}
QPushButton[buttonRole="validationIssue"]:hover {{
    background: {c["primary_soft"]};
    border-color: #bfdbfe;
}}
QPushButton[buttonRole="validationIssue"][issueSeverity="error"] {{
    border-left: 4px solid {c["error"]};
}}
QPushButton[buttonRole="validationIssue"][issueSeverity="warning"] {{
    border-left: 4px solid {c["warning"]};
}}
QLabel#AdvancedWarning {{
    color: #92400e;
    background: {c["warning_soft"]};
    border: 1px solid #fed7aa;
    border-radius: {r["md"]}px;
    padding: 9px 10px;
    font-weight: 600;
}}
QToolButton#InfoButton {{
    background: {c["primary_soft"]};
    color: {c["primary"]};
    border: 1px solid #bfdbfe;
    border-radius: 14px;
    font-size: 9.5pt;
    font-weight: 700;
    min-width: 28px;
    min-height: 28px;
    padding: 0px;
}}
QToolButton#InfoButton:hover {{
    background: #dbeafe;
    border-color: #93c5fd;
}}
QToolButton#InfoButton:pressed {{
    background: #bfdbfe;
}}
QLineEdit,
QPlainTextEdit,
QListWidget,
QTreeWidget,
QComboBox,
QSpinBox,
QDoubleSpinBox {{
    background: {c["surface"]};
    color: {c["text"]};
    border: 1px solid {c["border_strong"]};
    border-radius: {r["md"]}px;
    padding: {s["field_v"]}px {s["field_h"]}px;
    selection-background-color: #bfdbfe;
    selection-color: {c["text"]};
}}
QLineEdit:hover,
QPlainTextEdit:hover,
QComboBox:hover,
QSpinBox:hover,
QDoubleSpinBox:hover {{
    border-color: #94a3b8;
}}
QLineEdit:focus,
QPlainTextEdit:focus,
QListWidget:focus,
QTreeWidget:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {{
    border-color: {c["primary"]};
}}
QLineEdit:disabled,
QPlainTextEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {{
    background: #f1f5f9;
    color: {c["text_soft"]};
    border-color: {c["border"]};
}}
QLineEdit[validationState="error"],
QPlainTextEdit[validationState="error"],
QComboBox[validationState="error"],
QSpinBox[validationState="error"],
QDoubleSpinBox[validationState="error"] {{
    border-color: {c["error"]};
    background: #fffafa;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QAbstractItemView {{
    background: {c["surface"]};
    color: {c["text"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    selection-background-color: {c["primary_soft"]};
    selection-color: {c["primary_pressed"]};
}}
QListWidget::item,
QTreeWidget::item {{
    padding: 6px 8px;
    border-radius: {r["sm"]}px;
}}
QListWidget::item:selected,
QTreeWidget::item:selected {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
}}
QListWidget::item:hover:!selected,
QTreeWidget::item:hover:!selected {{
    background: {c["surface_muted"]};
}}
QListWidget#SceneEntityList {{
    padding: 4px;
}}
QListWidget#SceneEntityList::item {{
    padding: 5px 4px;
}}
QListWidget#RecentProjectsList::item {{
    padding: 10px 8px;
    margin: 2px 0;
}}
QListWidget#RecentProjectsList::item:selected {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
}}
QTreeWidget#ProjectExplorer {{
    background: transparent;
    border: none;
    outline: none;
}}
QTreeWidget#ProjectExplorer::item {{
    border-radius: {r["md"]}px;
    padding: 8px 10px;
    margin: 2px 0;
}}
QTreeWidget#ProjectExplorer::item:selected {{
    background: {c["primary_soft"]};
    color: {c["primary_pressed"]};
}}
QSplitter::handle {{
    background: transparent;
}}
QSplitter::handle:horizontal {{
    width: 8px;
    margin: 0 2px;
    border-left: 1px solid {c["border"]};
}}
QSplitter::handle:vertical {{
    height: 8px;
    margin: 2px 0;
    border-top: 1px solid {c["border"]};
}}
QSplitter::handle:hover:horizontal,
QSplitter::handle:pressed:horizontal {{
    border-left-color: #93c5fd;
    background: {c["primary_soft"]};
}}
QSplitter::handle:hover:vertical,
QSplitter::handle:pressed:vertical {{
    border-top-color: #93c5fd;
    background: {c["primary_soft"]};
}}
QTabWidget::pane {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    top: -1px;
}}
QTabWidget#WorkbenchTabs::pane,
QTabWidget#DetailTabs::pane {{
    background: {c["surface"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
}}
QTabBar::tab {{
    background: transparent;
    color: {c["text_muted"]};
    border: 1px solid transparent;
    border-bottom: none;
    padding: 8px 13px;
    margin-right: 4px;
    border-top-left-radius: {r["md"]}px;
    border-top-right-radius: {r["md"]}px;
}}
QTabBar::tab:hover:!selected {{
    background: {c["surface_muted"]};
    color: {c["text"]};
}}
QTabBar::tab:selected {{
    background: {c["surface"]};
    color: {c["primary_pressed"]};
    border: 1px solid {c["border"]};
    border-bottom: 1px solid {c["surface"]};
}}
QGroupBox {{
    background: {c["surface_alt"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    margin-top: 10px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: {c["text"]};
}}
QCheckBox {{
    color: {c["text"]};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {c["border_strong"]};
    border-radius: 4px;
    background: {c["surface"]};
}}
QCheckBox::indicator:hover {{
    border-color: #94a3b8;
}}
QCheckBox::indicator:checked {{
    background: {c["primary"]};
    border-color: {c["primary"]};
}}
QCheckBox::indicator:disabled {{
    background: #f1f5f9;
    border-color: {c["border"]};
}}
QStatusBar {{
    background: {c["surface"]};
    color: {c["text_muted"]};
    border-top: 1px solid {c["border"]};
}}
QLabel#StatusPill,
QLabel#StatusBadge {{
    background: {c["info_soft"]};
    color: #075985;
    border: 1px solid #bae6fd;
    border-radius: {r["md"]}px;
    padding: 4px 8px;
    font-weight: 600;
}}
QLabel#StatusPill[statusTone="neutral"],
QLabel#StatusBadge[statusTone="neutral"] {{
    background: {c["surface_muted"]};
    color: {c["text_muted"]};
    border-color: {c["border"]};
}}
QLabel#StatusPill[statusTone="success"],
QLabel#StatusBadge[statusTone="success"] {{
    background: {c["success_soft"]};
    color: #166534;
    border-color: #bbf7d0;
}}
QLabel#StatusPill[statusTone="warning"],
QLabel#StatusBadge[statusTone="warning"] {{
    background: {c["warning_soft"]};
    color: #92400e;
    border-color: #fed7aa;
}}
QLabel#StatusPill[statusTone="error"],
QLabel#StatusBadge[statusTone="error"] {{
    background: {c["error_soft"]};
    color: #991b1b;
    border-color: #fecaca;
}}
QLabel#StatusPill[statusTone="info"],
QLabel#StatusBadge[statusTone="info"] {{
    background: {c["info_soft"]};
    color: #075985;
    border-color: #bae6fd;
}}
QLabel#StatusDetail {{
    color: {c["text_muted"]};
    padding: 0 4px;
}}
QLabel#SimulationAdvancedHint {{
    color: {c["text_muted"]};
    background: {c["surface_alt"]};
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
    padding: 8px 10px;
}}
QProgressBar#RunStageProgress {{
    background: {c["surface_alt"]};
    border: 1px solid {c["border"]};
    border-radius: {r["sm"]}px;
    min-height: 8px;
    max-height: 10px;
}}
QProgressBar#RunStageProgress::chunk {{
    background: {c["primary"]};
    border-radius: {r["sm"]}px;
}}
QLabel[toolbarRole="section"] {{
    color: {c["text_muted"]};
    font-size: 8.8pt;
    font-weight: 700;
}}
QLabel[toolbarRole="status"] {{
    color: {c["text_muted"]};
    font-size: 8.8pt;
}}
QFrame#MaterialSwatch {{
    border: 1px solid {c["border"]};
    border-radius: {r["md"]}px;
}}
"""


STYLESHEET = _build_stylesheet()


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(STYLESHEET)
