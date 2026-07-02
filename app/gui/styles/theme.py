"""Application theme stylesheets, applied app-wide. Visual styling only."""

from app.gui.styles.palette import DARK, LIGHT, VALID_THEMES


DARK_STYLESHEET = f"""
QWidget {{
    background-color: {DARK["app_bg"]};
    color: {DARK["text"]};
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {DARK["app_bg"]};
}}

QListWidget#Sidebar {{
    background-color: {DARK["sidebar_bg"]};
    border: none;
    border-right: 1px solid {DARK["border"]};
    outline: none;
    padding-top: 10px;
}}

QListWidget#Sidebar::item {{
    padding: 12px 16px;
    border-radius: 6px;
    margin: 3px 10px;
    color: #d7e3ee;
}}

QListWidget#Sidebar::item:selected {{
    background-color: #0d4f98;
    color: white;
    border-left: 3px solid #00a2ff;
}}

QListWidget#Sidebar::item:hover {{
    background-color: #10263a;
}}

QFrame#StatusCard, QFrame#PanelCard, QFrame#HeaderBar {{
    background-color: {DARK["card_bg"]};
    border: 1px solid {DARK["border"]};
    border-radius: 8px;
}}

QFrame#StatusCard:hover {{
    border: 1px solid {DARK["border_hover"]};
    background-color: {DARK["card_hover"]};
}}

QScrollBar:vertical {{
    background-color: {DARK["sidebar_bg"]};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: #1f3344;
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {DARK["border_hover"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {DARK["sidebar_bg"]};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: #1f3344;
    border-radius: 4px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {DARK["border_hover"]};
}}

QFrame#TopBar {{
    background-color: {DARK["topbar_bg"]};
    border: none;
    border-bottom: 1px solid {DARK["border"]};
}}

QFrame#ScanModeBadge {{
    background-color: {DARK["muted_panel"]};
    border: 1px solid #2a4861;
    border-radius: 6px;
}}

QPushButton {{
    background-color: {DARK["accent"]};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {DARK["accent_hover"]};
}}

QPushButton:disabled {{
    background-color: {DARK["button_disabled_bg"]};
    color: {DARK["text_disabled"]};
}}

QPushButton#SecondaryButton {{
    background-color: transparent;
    color: {DARK["text_muted"]};
    border: 1px solid {DARK["border_strong"]};
    border-radius: 4px;
    padding: 4px 12px;
}}

QPushButton#SecondaryButton:hover {{
    color: {DARK["text"]};
    border-color: {DARK["accent_border"]};
}}

QFrame#SafetyFrame {{
    background-color: {DARK["safety_bg"]};
    border: 1px solid {DARK["success_border"]};
    border-radius: 6px;
}}

QLabel#SuccessBadge {{
    color: {DARK["success"]};
    font-weight: bold;
    background-color: {DARK["safety_bg"]};
    border: 1px solid {DARK["success_border"]};
    border-radius: 4px;
    padding: 2px 8px;
}}

QGroupBox {{
    background-color: {DARK["app_bg"]};
    border: 1px solid {DARK["border_strong"]};
    border-radius: 8px;
    color: {DARK["text_secondary"]};
    font-weight: bold;
    margin-top: 10px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

QLineEdit, QComboBox, QSpinBox {{
    background-color: {DARK["input_bg"]};
    border: 1px solid {DARK["border_strong"]};
    border-radius: 4px;
    color: {DARK["text_secondary"]};
    padding: 4px 8px;
}}

QPlainTextEdit, QTextEdit {{
    background-color: {DARK["input_bg"]};
    color: {DARK["text"]};
    border: none;
}}

QStatusBar {{
    background-color: {DARK["topbar_bg"]};
    color: {DARK["text_muted"]};
    border-top: 1px solid {DARK["border"]};
}}
"""


LIGHT_STYLESHEET = f"""
QWidget {{
    background-color: {LIGHT["app_bg"]};
    color: {LIGHT["text"]};
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {LIGHT["app_bg"]};
}}

QListWidget#Sidebar {{
    background-color: {LIGHT["sidebar_bg"]};
    border: none;
    border-right: 1px solid {LIGHT["border"]};
    outline: none;
    padding-top: 10px;
}}

QListWidget#Sidebar::item {{
    padding: 12px 16px;
    border-radius: 6px;
    margin: 3px 10px;
    color: {LIGHT["text_muted"]};
}}

QListWidget#Sidebar::item:selected {{
    background-color: {LIGHT["accent_light"]};
    color: {LIGHT["accent"]};
    border-left: 3px solid {LIGHT["accent"]};
}}

QListWidget#Sidebar::item:hover {{
    background-color: {LIGHT["sidebar_hover"]};
}}

QFrame#StatusCard, QFrame#PanelCard, QFrame#HeaderBar {{
    background-color: {LIGHT["card_bg"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 8px;
}}

QFrame#StatusCard:hover {{
    border: 1px solid {LIGHT["accent_border"]};
    background-color: {LIGHT["card_hover"]};
}}

QScrollBar:vertical {{
    background-color: {LIGHT["secondary_bg"]};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {LIGHT["border"]};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {LIGHT["accent_border"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {LIGHT["secondary_bg"]};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {LIGHT["border"]};
    border-radius: 4px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {LIGHT["accent_border"]};
}}

QFrame#TopBar {{
    background-color: {LIGHT["card_bg"]};
    border: none;
    border-bottom: 1px solid {LIGHT["border"]};
}}

QFrame#ScanModeBadge {{
    background-color: {LIGHT["accent_light"]};
    border: 1px solid {LIGHT["accent_border"]};
    border-radius: 6px;
}}

QPushButton {{
    background-color: {LIGHT["accent"]};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {LIGHT["accent_hover"]};
}}

QPushButton:disabled {{
    background-color: {LIGHT["button_secondary"]};
    color: {LIGHT["text_disabled"]};
}}

QPushButton#SecondaryButton {{
    background-color: {LIGHT["button_secondary"]};
    color: {LIGHT["text"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 4px;
    padding: 4px 12px;
}}

QPushButton#SecondaryButton:hover {{
    background-color: {LIGHT["button_secondary_hover"]};
    color: {LIGHT["text_heading"]};
    border-color: {LIGHT["accent_border"]};
}}

QFrame#SafetyFrame {{
    background-color: {LIGHT["secondary_bg"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 6px;
}}

QLabel#SuccessBadge {{
    color: {LIGHT["success"]};
    font-weight: bold;
    background-color: {LIGHT["secondary_bg"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 4px;
    padding: 2px 8px;
}}

QGroupBox {{
    background-color: {LIGHT["card_bg"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 8px;
    color: {LIGHT["text_heading"]};
    font-weight: bold;
    margin-top: 10px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

QLineEdit, QComboBox, QSpinBox {{
    background-color: {LIGHT["card_bg"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 4px;
    color: {LIGHT["text"]};
    padding: 4px 8px;
}}

QLineEdit:read-only {{
    background-color: {LIGHT["secondary_bg"]};
    color: {LIGHT["text_secondary"]};
}}

QPlainTextEdit, QTextEdit {{
    background-color: {LIGHT["secondary_bg"]};
    color: {LIGHT["text"]};
    border: none;
}}

QStatusBar {{
    background-color: {LIGHT["card_bg"]};
    color: {LIGHT["text_secondary"]};
    border-top: 1px solid {LIGHT["border"]};
}}
"""


def normalize_theme(theme: str | None) -> str:
    return theme if theme in VALID_THEMES else "dark"


def get_stylesheet(theme: str | None) -> str:
    return LIGHT_STYLESHEET if normalize_theme(theme) == "light" else DARK_STYLESHEET
