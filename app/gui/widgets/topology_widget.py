from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

# Dummy nodes only — replaced by real ARP/ping discovery in Faza 12 (Topology v1).
_DUMMY_NODES = [
    {"icon": "🖥", "name": "NOVI", "ip": "192.168.100.55", "tag": "Ovaj računar", "tag_color": "#58a6ff"},
    {"icon": "🌐", "name": "Router / Gateway", "ip": "192.168.100.1", "tag": "Aktivan", "tag_color": "#3fb950"},
    {"icon": "🖥", "name": "RADOVAN", "ip": "192.168.100.155", "tag": "Online", "tag_color": "#3fb950"},
    {"icon": "🖨", "name": "Canon iR1133iF", "ip": "192.168.100.50", "tag": "Štampač", "tag_color": "#a371f7"},
]

_LEGEND = [
    ("#3fb950", "Online"),
    ("#f85149", "Offline"),
    ("#8b949e", "Unknown"),
    ("#a371f7", "Printer"),
    ("#58a6ff", "Server"),
]


def _build_node(icon: str, name: str, ip: str, tag: str, tag_color: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("StatusCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 10)

    top_row = QHBoxLayout()
    icon_label = QLabel(icon)
    icon_label.setStyleSheet("font-size: 18px;")
    name_label = QLabel(name)
    name_label.setStyleSheet("font-weight: bold;")
    top_row.addWidget(icon_label)
    top_row.addWidget(name_label)
    top_row.addStretch(1)
    layout.addLayout(top_row)

    ip_label = QLabel(ip)
    ip_label.setStyleSheet("color: #9aa4b2;")
    layout.addWidget(ip_label)

    tag_label = QLabel(tag)
    tag_label.setStyleSheet(f"color: {tag_color}; font-weight: bold;")
    layout.addWidget(tag_label)

    return frame


def _build_arrow() -> QLabel:
    arrow = QLabel("→")
    arrow.setStyleSheet("color: #4b5566; font-size: 18px;")
    arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return arrow


def _build_legend() -> QHBoxLayout:
    row = QHBoxLayout()
    for color, label in _LEGEND:
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color};")
        text = QLabel(label)
        text.setStyleSheet("color: #9aa4b2;")
        row.addWidget(dot)
        row.addWidget(text)
        row.addSpacing(12)
    row.addStretch(1)
    return row


class NetworkTopologyWidget(QFrame):
    """Compact topology panel embedded in the Dashboard.

    Display-only with dummy nodes — Faza 12 (Topology v1) replaces _DUMMY_NODES
    with real ARP/ping discovery results. "Refresh" / "Open Network Map" are
    inert placeholders, same as the dashboard's other not-yet-wired buttons.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        header_row = QHBoxLayout()
        title = QLabel("Network Topology (detektovani uređaji na mreži)")
        title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        refresh_label = QLabel("⟳ Refresh")
        refresh_label.setStyleSheet("color: #58a6ff;")
        header_row.addWidget(refresh_label)
        layout.addLayout(header_row)

        nodes_row = QHBoxLayout()
        for index, node in enumerate(_DUMMY_NODES):
            nodes_row.addWidget(_build_node(**node))
            if index < len(_DUMMY_NODES) - 1:
                nodes_row.addWidget(_build_arrow())
        layout.addLayout(nodes_row)

        bottom_row = QHBoxLayout()
        bottom_row.addLayout(_build_legend())
        open_map_button = QPushButton("Open Network Map")
        bottom_row.addWidget(open_map_button)
        layout.addLayout(bottom_row)
