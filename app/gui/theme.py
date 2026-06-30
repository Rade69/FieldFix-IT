"""Dark theme stylesheet, applied app-wide. Visual styling only — no logic here."""

DARK_STYLESHEET = """
QWidget {
    background-color: #11151c;
    color: #e6e6e6;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #11151c;
}

QListWidget#Sidebar {
    background-color: #161a23;
    border: none;
    outline: none;
    padding-top: 8px;
}

QListWidget#Sidebar::item {
    padding: 10px 16px;
    border-radius: 6px;
    margin: 2px 8px;
}

QListWidget#Sidebar::item:selected {
    background-color: #1f6feb;
    color: white;
}

QListWidget#Sidebar::item:hover {
    background-color: #1c2230;
}

QFrame#StatusCard, QFrame#PanelCard, QFrame#HeaderBar {
    background-color: #161a23;
    border: 1px solid #232a36;
    border-radius: 8px;
}

QFrame#TopBar {
    background-color: #161a23;
    border: none;
    border-bottom: 1px solid #232a36;
}

QFrame#ScanModeBadge {
    border: 1px solid #2d3645;
    border-radius: 6px;
}

QPushButton {
    background-color: #1f6feb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #388bfd;
}

QStatusBar {
    background-color: #161a23;
    color: #9aa4b2;
    border-top: 1px solid #232a36;
}
"""
