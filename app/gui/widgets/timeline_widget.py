from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

# Dummy data only — replaced by real scan event log (Faza 11+).
_DUMMY_EVENTS = [
    ("14:23:01", "✓", "#3fb950", "Network scan complete", "4 devices found"),
    ("14:23:05", "✓", "#3fb950", "SMB scan complete", "Sharing enabled"),
    ("14:23:08", "⚠", "#d29922", "Firewall check", "2 rules inactive"),
    ("14:23:10", "✓", "#3fb950", "Services check", "All critical running"),
    ("14:23:12", "✓", "#3fb950", "Printer scan", "2 printers found"),
    ("14:22:47", "✓", "#3fb950", "Connection test", "Host reachable"),
    ("14:22:30", "✓", "#3fb950", "Scan started", "Full diagnostic"),
]


def _build_row(time: str, icon: str, icon_color: str, message: str, detail: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(10)

    time_label = QLabel(time)
    time_label.setStyleSheet("color: #9aa4b2; font-size: 11px; font-family: monospace;")
    time_label.setFixedWidth(56)
    row.addWidget(time_label)

    icon_label = QLabel(icon)
    icon_label.setStyleSheet(f"color: {icon_color};")
    icon_label.setFixedWidth(16)
    row.addWidget(icon_label)

    msg_label = QLabel(message)
    msg_label.setStyleSheet("font-weight: bold;")
    row.addWidget(msg_label)

    row.addStretch(1)

    detail_label = QLabel(detail)
    detail_label.setStyleSheet("color: #9aa4b2; font-size: 11px;")
    row.addWidget(detail_label)

    return row


class ActivityTimelineWidget(QFrame):
    """Activity Timeline panel. Dummy events — replaced by real scan log (Faza 11)."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        title = QLabel("📋 Activity Timeline")
        title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        clear_link = QLabel("⟲ Clear")
        clear_link.setStyleSheet("color: #58a6ff;")
        header_row.addWidget(clear_link)
        layout.addLayout(header_row)

        for time, icon, color, message, detail in _DUMMY_EVENTS:
            layout.addLayout(_build_row(time, icon, color, message, detail))

        layout.addStretch(1)
