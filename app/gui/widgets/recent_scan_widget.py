from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

# Dummy data only — replaced by real scan results once modules are wired (Faza 4+).
# status: "ok" | "fail" | "info"
_DUMMY_ROWS = [
    ("Ping Gateway (192.168.100.1)", "OK", "ok"),
    ("Ping 192.168.100.155 (RADOVAN)", "OK", "ok"),
    ("SMB Port (445)", "OK", "ok"),
    ("File and Printer Sharing (FW)", "DISABLED", "fail"),
    ("Network Discovery (FW)", "DISABLED", "fail"),
    ("LanmanServer Service", "Running", "ok"),
    ("LanmanWorkstation Service", "Running", "ok"),
    ("FDResPub Service", "Running", "ok"),
    ("Print Spooler", "Running", "ok"),
    ("Shared Printers Found", "2", "info"),
]

_STATUS_STYLE = {
    "ok": ("✓", "#3fb950"),
    "fail": ("✕", "#f85149"),
    "info": ("●", "#a371f7"),
}


def _build_row(label: str, value: str, status: str) -> QHBoxLayout:
    icon, color = _STATUS_STYLE[status]
    row = QHBoxLayout()
    icon_label = QLabel(icon)
    icon_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    text_label = QLabel(label)
    value_label = QLabel(value)
    value_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    row.addWidget(icon_label)
    row.addWidget(text_label)
    row.addStretch(1)
    row.addWidget(value_label)
    return row


class RecentScanWidget(QFrame):
    """Recent Scan Summary panel. Dummy rows — real wiring starts once modules exist (Faza 4+)."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        header_row = QHBoxLayout()
        title = QLabel("Recent Scan Summary")
        title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        refresh_label = QLabel("⟳")
        refresh_label.setStyleSheet("color: #58a6ff;")
        header_row.addWidget(refresh_label)
        layout.addLayout(header_row)

        for label, value, status in _DUMMY_ROWS:
            layout.addLayout(_build_row(label, value, status))

        footer = QLabel("🕒 Last scan: 29.06.2026 15:30:22")
        footer.setStyleSheet("color: #9aa4b2; margin-top: 4px;")
        layout.addWidget(footer)
