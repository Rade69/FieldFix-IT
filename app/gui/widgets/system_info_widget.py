from __future__ import annotations

import ipaddress
import struct
import sys

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.modules.network.models import NetworkData


def _prefix_to_mask(prefix: int) -> str:
    mask = (0xFFFFFFFF >> (32 - prefix)) << (32 - prefix)
    return ".".join(str((mask >> (8 * i)) & 0xFF) for i in (3, 2, 1, 0))


def _is_ipv4(ip: str) -> bool:
    try:
        return isinstance(ipaddress.ip_address(ip), ipaddress.IPv4Address)
    except ValueError:
        return False


def _os_string() -> str:
    v = sys.getwindowsversion()
    if v.build >= 22000:
        return f"Windows 11 (Build {v.build})"
    return f"Windows {v.major}.{v.minor} (Build {v.build})"


def _get_rows(network: NetworkData | None) -> list[tuple[str, str, str]]:
    if network is None:
        return [("🖥", "Status", "Click 'Run Diagnostics'")]

    rows: list[tuple[str, str, str]] = []
    rows.append(("🖥", "Computer Name", network.hostname or "—"))
    rows.append(("🪟", "OS", _os_string()))

    ipv4 = next((ip for ip in network.ip_addresses if _is_ipv4(ip.ip_address)), None)
    if ipv4:
        rows.append(("📡", "IPv4 Address", ipv4.ip_address))
        if ipv4.prefix_length:
            rows.append(("🌐", "Subnet Mask", _prefix_to_mask(ipv4.prefix_length)))

    if network.gateways:
        gw = network.gateways[0]
        suffix = " ✓" if network.gateway_reachable else (" ✕" if network.gateway_reachable is False else "")
        rows.append(("🔀", "Default Gateway", gw.next_hop + suffix))

    if network.dns:
        servers: list[str] = []
        for d in network.dns:
            servers.extend(d.servers)
        unique = list(dict.fromkeys(servers))
        if unique:
            rows.append(("🌐", "DNS Servers", ", ".join(unique[:3])))

    if network.profiles:
        rows.append(("📶", "Network Profile", network.profiles[0].category))

    if network.adapters:
        a = network.adapters[0]
        rows.append(("📶", "Adapter", a.description or a.name))
        if a.mac_address:
            rows.append(("🔗", "MAC Address", a.mac_address))

    return rows


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


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if w := item.widget():
            w.deleteLater()
        elif child := item.layout():
            _clear_layout(child)


class SystemInfoWidget(QFrame):
    """System & Network Info panel. Shows dummy rows until update_data() is called."""

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

        self._content = QVBoxLayout()
        layout.addLayout(self._content)
        self.update_data(None)

    def update_data(self, network: NetworkData | None) -> None:
        _clear_layout(self._content)
        for icon, key, value in _get_rows(network):
            self._content.addLayout(_build_row(icon, key, value))
