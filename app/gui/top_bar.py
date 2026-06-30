from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.gui.icons import APP_ICON_32

# Dummy data only — same fields as docs/target_gui.md status header.
_LEFT_LINE1 = "Computer: <b>NOVI</b>"
_LEFT_LINE2 = "Windows 11 Pro 23H2 (22631.3296) &nbsp;&nbsp; User: dm &nbsp;&nbsp; Uptime: 2h 15m"
_RIGHT_LINE1 = "IP: <b>192.168.100.55</b>"
_RIGHT_LINE2 = 'Network: <span style="color:#3fb950;"><b>Private</b></span>'


def _rich_label(html: str, muted: bool = False) -> QLabel:
    label = QLabel(html)
    label.setTextFormat(Qt.TextFormat.RichText)
    if muted:
        label.setStyleSheet("color: #9aa4b2; font-size: 11px;")
    return label


def _info_block(line1_html: str, line2_html: str) -> QVBoxLayout:
    column = QVBoxLayout()
    column.setSpacing(2)
    column.addWidget(_rich_label(line1_html))
    column.addWidget(_rich_label(line2_html, muted=True))
    return column


class TopBar(QFrame):
    """Global header bar spanning the full window width, above sidebar + content.

    Dummy data only (docs/target_gui.md) — Settings / Start New Scan are inert
    placeholders, same as the dashboard's other not-yet-wired buttons.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(str(APP_ICON_32)).scaled(
            32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))
        layout.addWidget(icon_label)
        layout.addSpacing(8)

        logo_column = QVBoxLayout()
        logo_column.setSpacing(2)
        title = QLabel("FieldFix IT")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        subtitle = _rich_label("Windows IT Diagnostics", muted=True)
        logo_column.addWidget(title)
        logo_column.addWidget(subtitle)
        layout.addLayout(logo_column)
        layout.addSpacing(28)

        layout.addLayout(_info_block(_LEFT_LINE1, _LEFT_LINE2))
        layout.addSpacing(28)
        layout.addLayout(_info_block(_RIGHT_LINE1, _RIGHT_LINE2))
        layout.addStretch(1)

        scan_mode = QFrame()
        scan_mode.setObjectName("ScanModeBadge")
        scan_mode_layout = QVBoxLayout(scan_mode)
        scan_mode_layout.setContentsMargins(10, 4, 10, 4)
        scan_mode_layout.setSpacing(0)
        scan_mode_layout.addWidget(_rich_label("🛡 Scan Mode", muted=True))
        scan_mode_value = QLabel("Read Only")
        scan_mode_value.setStyleSheet("color: #3fb950; font-weight: bold;")
        scan_mode_layout.addWidget(scan_mode_value)
        layout.addWidget(scan_mode)
        layout.addSpacing(16)

        settings_label = QLabel("⚙ Settings")
        settings_label.setStyleSheet("color: #9aa4b2;")
        layout.addWidget(settings_label)
        layout.addSpacing(16)

        start_scan_button = QPushButton("▶ Start New Scan ▾")
        layout.addWidget(start_scan_button)
