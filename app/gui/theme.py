"""Application theme stylesheets, applied app-wide. Visual styling only."""

DARK_STYLESHEET = """
QWidget {
    background-color: #071018;
    color: #f0f6fc;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #071018;
}

QListWidget#Sidebar {
    background-color: #081522;
    border: none;
    border-right: 1px solid #1f3344;
    outline: none;
    padding-top: 10px;
}

QListWidget#Sidebar::item {
    padding: 12px 16px;
    border-radius: 6px;
    margin: 3px 10px;
    color: #d7e3ee;
}

QListWidget#Sidebar::item:selected {
    background-color: #0d4f98;
    color: white;
    border-left: 3px solid #00a2ff;
}

QListWidget#Sidebar::item:hover {
    background-color: #10263a;
}

QFrame#StatusCard, QFrame#PanelCard, QFrame#HeaderBar {
    background-color: #0d1b27;
    border: 1px solid #203447;
    border-radius: 8px;
}

QFrame#StatusCard:hover {
    border: 1px solid #2d5480;
    background-color: #101f2e;
}

QScrollBar:vertical {
    background-color: #081522;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #1f3344;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #2d5480;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #081522;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #1f3344;
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #2d5480;
}

QFrame#TopBar {
    background-color: #06111b;
    border: none;
    border-bottom: 1px solid #203447;
}

QFrame#ScanModeBadge {
    background-color: #0b1d2c;
    border: 1px solid #2a4861;
    border-radius: 6px;
}

QPushButton {
    background-color: #0969da;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1f8bff;
}

QPushButton:disabled {
    background-color: #1c2a38;
    color: #7d8b99;
}

QPushButton#SecondaryButton {
    background-color: transparent;
    color: #9aa4b2;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 12px;
}

QPushButton#SecondaryButton:hover {
    color: #f0f6fc;
    border-color: #58a6ff;
}

QFrame#SafetyFrame {
    background-color: #0d2217;
    border: 1px solid #1a4731;
    border-radius: 6px;
}

QLabel#SuccessBadge {
    color: #3fb950;
    font-weight: bold;
    background-color: #0d2217;
    border: 1px solid #1a4731;
    border-radius: 4px;
    padding: 2px 8px;
}

QGroupBox {
    background-color: #071018;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #c9d1d9;
    font-weight: bold;
    margin-top: 10px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    color: #c9d1d9;
    padding: 4px 8px;
}

QStatusBar {
    background-color: #06111b;
    color: #9aa4b2;
    border-top: 1px solid #203447;
}
"""


LIGHT_STYLESHEET = """
QWidget {
    background-color: #F5F7FA;
    color: #1F2937;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #F5F7FA;
}

QListWidget#Sidebar {
    background-color: #F8FAFC;
    border: none;
    border-right: 1px solid #D8E0EA;
    outline: none;
    padding-top: 10px;
}

QListWidget#Sidebar::item {
    padding: 12px 16px;
    border-radius: 6px;
    margin: 3px 10px;
    color: #334155;
}

QListWidget#Sidebar::item:selected {
    background-color: #DBEAFE;
    color: #2563EB;
    border-left: 3px solid #2563EB;
}

QListWidget#Sidebar::item:hover {
    background-color: #EEF4FF;
}

QFrame#StatusCard, QFrame#PanelCard, QFrame#HeaderBar {
    background-color: #FFFFFF;
    border: 1px solid #D8E0EA;
    border-radius: 8px;
}

QFrame#StatusCard:hover {
    border: 1px solid #93C5FD;
    background-color: #F8FAFC;
}

QScrollBar:vertical {
    background-color: #EEF2F7;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #D8E0EA;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #93C5FD;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #EEF2F7;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #D8E0EA;
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #93C5FD;
}

QFrame#TopBar {
    background-color: #FFFFFF;
    border: none;
    border-bottom: 1px solid #D8E0EA;
}

QFrame#ScanModeBadge {
    background-color: #DBEAFE;
    border: 1px solid #93C5FD;
    border-radius: 6px;
}

QPushButton {
    background-color: #2563EB;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:disabled {
    background-color: #E5E7EB;
    color: #9CA3AF;
}

QPushButton#SecondaryButton {
    background-color: #E5E7EB;
    color: #1F2937;
    border: 1px solid #D8E0EA;
    border-radius: 4px;
    padding: 4px 12px;
}

QPushButton#SecondaryButton:hover {
    background-color: #D1D5DB;
    color: #111827;
    border-color: #93C5FD;
}

QFrame#SafetyFrame {
    background-color: #EEF2F7;
    border: 1px solid #D8E0EA;
    border-radius: 6px;
}

QLabel#SuccessBadge {
    color: #16A34A;
    font-weight: bold;
    background-color: #EEF2F7;
    border: 1px solid #D8E0EA;
    border-radius: 4px;
    padding: 2px 8px;
}

QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #D8E0EA;
    border-radius: 8px;
    color: #111827;
    font-weight: bold;
    margin-top: 10px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #D8E0EA;
    border-radius: 4px;
    color: #1F2937;
    padding: 4px 8px;
}

QLineEdit:read-only {
    background-color: #EEF2F7;
    color: #6B7280;
}

QStatusBar {
    background-color: #FFFFFF;
    color: #6B7280;
    border-top: 1px solid #D8E0EA;
}
"""

VALID_THEMES = {"dark", "light"}


def normalize_theme(theme: str | None) -> str:
    return theme if theme in VALID_THEMES else "dark"


def get_stylesheet(theme: str | None) -> str:
    return LIGHT_STYLESHEET if normalize_theme(theme) == "light" else DARK_STYLESHEET
