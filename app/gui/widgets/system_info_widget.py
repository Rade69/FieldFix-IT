from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

# Dummy data only — replaced by real Network module results in Faza 4.
_DUMMY_ROWS = [
    ("🖥", "Computer Name", "NOVI"),
    ("🌐", "Domain / Workgroup", "WORKGROUP"),
    ("🪟", "OS", "Windows 11 Pro 23H2 (22631.3296)"),
    ("📡", "IPv4 Address", "192.168.100.55"),
    ("🌐", "Subnet Mask", "255.255.255.0"),
    ("🔀", "Default Gateway", "192.168.100.1"),
    ("🌐", "DNS Servers", "1.1.1.1, 8.8.8.8"),
    ("📶", "Network Profile", "Private"),
    ("🔗", "MAC Address", "24-5E-BE-12-34-56"),
    ("📶", "Adapter", "Intel(R) Ethernet Connection (7) I219-V"),
]


def _build_row(icon: str, key: str, value: str) -> QHBoxLayout:
    row = QHBoxLayout()
    icon_label = QLabel(icon)
    key_label = QLabel(key)
    key_label.setStyleSheet("color: #9aa4b2;")
    value_label = QLabel(value)
    value_label.setStyleSheet("font-weight: bold;")
    row.addWidget(icon_label)
    row.addWidget(key_label)
    row.addStretch(1)
    row.addWidget(value_label)
    return row


class SystemInfoWidget(QFrame):
    """System & Network Info panel. Dummy rows — Faza 4 (Network module) provides real values."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        header_row = QHBoxLayout()
        title = QLabel("System & Network Info")
        title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        refresh_label = QLabel("⟳ Refresh")
        refresh_label.setStyleSheet("color: #58a6ff;")
        header_row.addWidget(refresh_label)
        layout.addLayout(header_row)

        for icon, key, value in _DUMMY_ROWS:
            layout.addLayout(_build_row(icon, key, value))
