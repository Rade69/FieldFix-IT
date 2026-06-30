from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.modules.network.models import NetworkData
from app.modules.printers.models import PrintersData

_IP_RE = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

_LEGEND = [
    ("#3fb950", "Online"),
    ("#f85149", "Offline"),
    ("#8b949e", "Unknown"),
    ("#a371f7", "Printer"),
    ("#58a6ff", "Server"),
]


def _extract_ip(text: str) -> str | None:
    m = _IP_RE.search(text)
    return m.group(0) if m else None


def _nodes_from_scan(
    network: NetworkData, printers: PrintersData | None
) -> list[dict]:
    local_ips = {ip.ip_address for ip in network.ip_addresses if ip.ip_address}
    local_ip = next(iter(local_ips), "")
    gateway_ip = network.gateways[0].next_hop if network.gateways else ""
    seen: set[str] = set(local_ips)
    nodes: list[dict] = []

    # This PC
    nodes.append({
        "icon": "🖥", "name": network.hostname or "This PC", "ip": local_ip,
        "tag": "This PC", "tag_color": "#58a6ff",
    })

    # Gateway
    if gateway_ip:
        seen.add(gateway_ip)
        ok = network.gateway_reachable
        nodes.append({
            "icon": "🌐", "name": "Router / Gateway", "ip": gateway_ip,
            "tag": "Active" if ok else ("Unreachable" if ok is False else "Unknown"),
            "tag_color": "#3fb950" if ok else ("#f85149" if ok is False else "#8b949e"),
        })

    # Network printers (detect IP from port_name)
    if printers:
        for p in printers.printers:
            ip = _extract_ip(p.port_name) if p.port_name else None
            if ip and ip not in seen:
                seen.add(ip)
                nodes.append({
                    "icon": "🖨", "name": p.name, "ip": ip,
                    "tag": "Printer", "tag_color": "#a371f7",
                })

    # ARP entries (remaining reachable devices)
    for entry in network.arp_entries:
        if entry.ip_address in seen:
            continue
        if entry.state not in ("Reachable", "Stale"):
            continue
        seen.add(entry.ip_address)
        nodes.append({
            "icon": "🖥", "name": entry.ip_address, "ip": entry.ip_address,
            "tag": "Online" if entry.state == "Reachable" else "Unknown",
            "tag_color": "#3fb950" if entry.state == "Reachable" else "#8b949e",
        })
        if len(nodes) >= 8:
            break

    return nodes


def _build_node(icon: str, name: str, ip: str, tag: str, tag_color: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("StatusCard")
    frame.setFixedWidth(160)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(4)

    icon_lbl = QLabel(icon)
    icon_lbl.setStyleSheet("font-size: 22px;")
    layout.addWidget(icon_lbl)

    name_lbl = QLabel(name)
    name_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
    name_lbl.setWordWrap(True)
    layout.addWidget(name_lbl)

    ip_lbl = QLabel(ip or "—")
    ip_lbl.setStyleSheet("color: #9aa4b2; font-size: 11px;")
    layout.addWidget(ip_lbl)

    tag_lbl = QLabel(tag)
    tag_lbl.setStyleSheet(f"color: {tag_color}; font-weight: bold; font-size: 11px;")
    layout.addWidget(tag_lbl)

    return frame


def _build_arrow() -> QLabel:
    arrow = QLabel("→")
    arrow.setStyleSheet("color: #2d4f6e; font-size: 22px;")
    arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
    arrow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
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


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if w := item.widget():
            w.deleteLater()
        elif child := item.layout():
            _clear_layout(child)


class NetworkTopologyWidget(QFrame):
    """Compact topology panel embedded in the Dashboard.

    Shows placeholder until update_data() is called after a scan.
    """

    open_topology = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("Network Topology (detected devices)")
        title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        refresh_btn = QPushButton("⟳ Refresh")
        refresh_btn.setFlat(True)
        refresh_btn.setStyleSheet(
            "QPushButton { color: #58a6ff; background: transparent; border: none;"
            " padding: 0; font-size: 12px; }"
            "QPushButton:hover { color: #79b8ff; }"
        )
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.open_topology)
        header_row.addWidget(refresh_btn)
        outer.addLayout(header_row)

        # Scrollable nodes area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setFixedHeight(130)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._nodes_container = QWidget()
        self._nodes_container.setStyleSheet("background: transparent;")
        self._nodes_row = QHBoxLayout(self._nodes_container)
        self._nodes_row.setContentsMargins(0, 0, 0, 0)
        self._nodes_row.setSpacing(8)
        self._scroll.setWidget(self._nodes_container)
        self._show_placeholder()
        outer.addWidget(self._scroll)

        bottom_row = QHBoxLayout()
        bottom_row.addLayout(_build_legend())
        open_map_btn = QPushButton("🗺  Open Network Map")
        open_map_btn.setStyleSheet(
            "QPushButton { background-color: #0d2840; color: #58a6ff; border: 1px solid #1f4060;"
            " border-radius: 6px; padding: 5px 14px; font-weight: 600; }"
            "QPushButton:hover { background-color: #102a4a; border-color: #2d6da8; color: #79b8ff; }"
        )
        open_map_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_map_btn.clicked.connect(self.open_topology)
        bottom_row.addWidget(open_map_btn)
        outer.addLayout(bottom_row)

    def _show_placeholder(self) -> None:
        lbl = QLabel("Run a scan to see network devices.")
        lbl.setStyleSheet("color: #9aa4b2; padding: 20px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._nodes_row.addWidget(lbl)
        self._nodes_row.addStretch(1)

    def update_data(
        self,
        network: NetworkData | None,
        printers: PrintersData | None = None,
    ) -> None:
        _clear_layout(self._nodes_row)

        if network is None:
            self._show_placeholder()
            return

        nodes = _nodes_from_scan(network, printers)

        if not nodes:
            lbl = QLabel("No network devices found.")
            lbl.setStyleSheet("color: #9aa4b2;")
            self._nodes_row.addWidget(lbl)
            self._nodes_row.addStretch(1)
            return

        for i, node in enumerate(nodes):
            self._nodes_row.addWidget(_build_node(**node))
            if i < len(nodes) - 1:
                self._nodes_row.addWidget(_build_arrow())
        self._nodes_row.addStretch(1)
