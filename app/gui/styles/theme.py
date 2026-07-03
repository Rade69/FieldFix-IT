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

QFrame#SummaryBanner {{
    background-color: #0a1929;
    border: none;
    border-bottom: 1px solid #1f6feb;
}}

QFrame#SeparatorLine {{
    color: {DARK["border_strong"]};
    background-color: {DARK["border_strong"]};
    max-height: 1px;
}}

QLabel#SummaryText {{
    color: #8fc7ff;
    font-size: 12px;
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

QPushButton#SecondaryButton:disabled {{
    background-color: {DARK["button_disabled_bg"]};
    color: {DARK["text_disabled"]};
    border-color: {DARK["border"]};
}}

QPushButton#PrimaryButton {{
    background-color: {DARK["accent"]};
    color: white;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {DARK["accent_hover"]};
}}

QPushButton#AccentButton {{
    background-color: #0d2840;
    color: {DARK["accent_border"]};
    border: 1px solid #1f4060;
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 600;
}}

QPushButton#AccentButton:hover {{
    background-color: #102a4a;
    border-color: #2d6da8;
    color: #79b8ff;
}}

QPushButton#LinkButton {{
    background: transparent;
    color: {DARK["text_muted"]};
    border: none;
}}

QPushButton#LinkButton:hover {{
    color: {DARK["accent_border"]};
}}

QPushButton#FilterPill {{
    background-color: transparent;
    color: {DARK["text_muted"]};
    border: 1px solid {DARK["border_strong"]};
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 11px;
}}

QPushButton#FilterPill:hover:!checked {{
    border-color: {DARK["text_muted"]};
    color: {DARK["text_muted"]};
}}

QPushButton#FilterPill:checked {{
    border-color: {DARK["accent_border"]};
    color: {DARK["accent_border"]};
    background-color: #0a1929;
}}

QLabel#VersionBadge {{
    color: #4b8bbe;
    background-color: #0d2840;
    border: 1px solid #1f4060;
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 10px;
}}

QFrame#ActiveScenarioCard {{
    background-color: {DARK["card_bg"]};
    border: 1px solid {DARK["accent"]};
    border-radius: 8px;
}}

QFrame#CodeBlock {{
    background-color: {DARK["input_bg"]};
    border: 1px solid {DARK["border_strong"]};
    border-radius: 4px;
}}

QLabel#CodeText {{
    color: #79c0ff;
    font-family: Consolas, monospace;
    font-size: 11px;
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

QSpinBox {{
    padding-right: 30px;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {DARK["muted_panel"]};
    border-left: 1px solid {DARK["border_strong"]};
    width: 24px;
    subcontrol-origin: border;
}}

QSpinBox::up-button {{
    subcontrol-position: top right;
    border-bottom: 1px solid {DARK["border"]};
    border-top-right-radius: 4px;
}}

QSpinBox::down-button {{
    subcontrol-position: bottom right;
    border-bottom-right-radius: 4px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {DARK["card_hover"]};
}}

QComboBox {{
    padding-right: 30px;
}}

QComboBox::drop-down {{
    background-color: {DARK["muted_panel"]};
    border-left: 1px solid {DARK["border_strong"]};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    width: 24px;
}}

QComboBox::drop-down:hover {{
    background-color: {DARK["card_hover"]};
}}

QPlainTextEdit, QTextEdit {{
    background-color: {DARK["input_bg"]};
    color: {DARK["text"]};
    border: none;
}}

QPlainTextEdit QWidget, QTextEdit QWidget {{
    background-color: {DARK["input_bg"]};
    color: {DARK["text"]};
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

QFrame#SummaryBanner {{
    background-color: {LIGHT["accent_light"]};
    border: none;
    border-bottom: 1px solid {LIGHT["accent_border"]};
}}

QFrame#SeparatorLine {{
    color: {LIGHT["border"]};
    background-color: {LIGHT["border"]};
    max-height: 1px;
}}

QLabel#SummaryText {{
    color: {LIGHT["accent"]};
    font-size: 12px;
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

QPushButton#SecondaryButton:disabled {{
    background-color: {LIGHT["button_secondary"]};
    color: {LIGHT["text_disabled"]};
    border-color: {LIGHT["border"]};
}}

QPushButton#PrimaryButton {{
    background-color: {LIGHT["accent"]};
    color: white;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {LIGHT["accent_hover"]};
}}

QPushButton#AccentButton {{
    background-color: {LIGHT["accent_light"]};
    color: {LIGHT["accent"]};
    border: 1px solid {LIGHT["accent_border"]};
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 600;
}}

QPushButton#AccentButton:hover {{
    background-color: #EEF4FF;
    border-color: {LIGHT["accent"]};
    color: {LIGHT["accent_hover"]};
}}

QPushButton#LinkButton {{
    background: transparent;
    color: {LIGHT["text_muted"]};
    border: none;
}}

QPushButton#LinkButton:hover {{
    color: {LIGHT["accent"]};
}}

QPushButton#FilterPill {{
    background-color: transparent;
    color: {LIGHT["text_secondary"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 11px;
}}

QPushButton#FilterPill:hover:!checked {{
    border-color: {LIGHT["accent_border"]};
    color: {LIGHT["text"]};
}}

QPushButton#FilterPill:checked {{
    border-color: {LIGHT["accent"]};
    color: {LIGHT["accent"]};
    background-color: {LIGHT["accent_light"]};
}}

QLabel#VersionBadge {{
    color: {LIGHT["accent"]};
    background-color: {LIGHT["accent_light"]};
    border: 1px solid {LIGHT["accent_border"]};
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 10px;
}}

QFrame#ActiveScenarioCard {{
    background-color: {LIGHT["card_bg"]};
    border: 1px solid {LIGHT["accent"]};
    border-radius: 8px;
}}

QFrame#CodeBlock {{
    background-color: {LIGHT["secondary_bg"]};
    border: 1px solid {LIGHT["border"]};
    border-radius: 4px;
}}

QLabel#CodeText {{
    color: {LIGHT["accent"]};
    font-family: Consolas, monospace;
    font-size: 11px;
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

QSpinBox {{
    padding-right: 30px;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {LIGHT["secondary_bg"]};
    border-left: 1px solid {LIGHT["border"]};
    width: 24px;
    subcontrol-origin: border;
}}

QSpinBox::up-button {{
    subcontrol-position: top right;
    border-bottom: 1px solid {LIGHT["border"]};
    border-top-right-radius: 4px;
}}

QSpinBox::down-button {{
    subcontrol-position: bottom right;
    border-bottom-right-radius: 4px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {LIGHT["button_secondary_hover"]};
}}

QComboBox {{
    padding-right: 30px;
}}

QComboBox::drop-down {{
    background-color: {LIGHT["secondary_bg"]};
    border-left: 1px solid {LIGHT["border"]};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    width: 24px;
}}

QComboBox::drop-down:hover {{
    background-color: {LIGHT["button_secondary_hover"]};
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

QPlainTextEdit QWidget, QTextEdit QWidget {{
    background-color: {LIGHT["secondary_bg"]};
    color: {LIGHT["text"]};
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
