"""Dark theme stylesheet, applied app-wide. Visual styling only — no logic here."""

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

QStatusBar {
    background-color: #06111b;
    color: #9aa4b2;
    border-top: 1px solid #203447;
}
"""
