"""Network Topology page — Inventory tab (default) + Map tab (graph)."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QGraphicsPathItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.modules.network.models import ArpEntry, DiscoveredDevice, NetworkData, OsFingerprint
from app.modules.network.scanner import NetworkScanner
from app.modules.network.subnet_scanner import SubnetScanner
from app.modules.printers.models import PrinterInfo, PrintersData
from app.modules.printers.scanner import PrintersScanner

# ── Map-view node palette ─────────────────────────────────────────────────────

_NODE_COLORS = {
    "pc":      "#1f6feb",
    "gateway": "#e65100",
    "device":  "#2e7d32",
    "printer": "#7b1fa2",
}
_NODE_BG = {
    "pc":      "#071f3d",
    "gateway": "#3d1500",
    "device":  "#0d2e1a",
    "printer": "#1e0938",
}
_NODE_ICONS = {
    "pc":      "🖥",
    "gateway": "🌐",
    "device":  "💻",
    "printer": "🖨",
}
_CARD_W    = 170
_CARD_H    = 124
_RADIUS    = 8
_NODE_V_GAP = 136
_COL_W     = 280


# ── Graph data helpers (kept intact — used by tests) ─────────────────────────

# Context: agent_reports/2026-07-01_topology-inventory-polish.md
def build_nodes(network: NetworkData, printers: PrintersData) -> list[dict]:
    """Build topology node list from scan data. IPv6 entries are excluded."""
    local_ips = {ip.ip_address for ip in network.ip_addresses if ip.ip_address}
    local_ip = next(iter(local_ips), "")
    gateway_ip = network.gateways[0].next_hop if network.gateways else ""
    local_os = network.local_os or OsFingerprint(
        name="Windows",
        confidence="MEDIUM",
        detected_by=("local app platform",),
    )

    nodes: list[dict] = [{
        "id": "pc",
        "label": network.hostname or "This PC",
        "sublabel": local_ip,
        "node_type": "pc",
        "os": local_os.name,
        "confidence": local_os.confidence,
        "detected_by": " + ".join(local_os.detected_by),
    }]

    if gateway_ip:
        nodes.append({
            "id": "gw",
            "label": "Gateway",
            "sublabel": gateway_ip,
            "node_type": "gateway",
            "os": "Network gateway / router",
            "confidence": "MEDIUM",
            "detected_by": "default route",
        })

    for entry in network.arp_entries:
        ip = entry.ip_address
        mac = (entry.mac_address or "").upper().replace(":", "-")
        if not ip or ":" in ip:
            continue
        if ip in local_ips or ip == gateway_ip:
            continue
        try:
            first, last = int(ip.split(".")[0]), int(ip.split(".")[-1])
        except (ValueError, IndexError):
            continue
        if first >= 224 or last in (0, 255):
            continue
        if mac.startswith("01-00-5E") or mac == "FF-FF-FF-FF-FF-FF":
            continue
        nodes.append({
            "id": f"arp_{entry.ip_address}",
            "label": entry.ip_address,
            "sublabel": entry.mac_address,
            "node_type": "device",
            "os": "Unknown",
            "confidence": "LOW",
            "detected_by": "ARP table only",
        })

    printer_count = 0
    for printer in printers.printers:
        # Include network printers: resolved IP, Connection type, or default
        has_network_ip = bool(printer.ip_address)
        if not has_network_ip and printer.printer_type not in ("Connection",) and not printer.is_default:
            continue
        nodes.append({
            "id": f"printer_{printer_count}",
            "label": printer.name[:18] if printer.name else "Printer",
            "sublabel": printer.ip_address or ("★ Default" if printer.is_default else printer.printer_type or ""),
            "node_type": "printer",
            "os": "Printer firmware",
            "confidence": "MEDIUM",
            "detected_by": "Windows printer inventory",
        })
        printer_count += 1
        if printer_count >= 4:
            break

    return nodes


def compute_positions(
    nodes: list[dict],
    canvas_w: int,
    canvas_h: int,
) -> dict[str, tuple[float, float]]:
    """Return {node_id: (cx, cy)} — center of each card."""
    del canvas_w
    center_y = canvas_h / 2
    positions: dict[str, tuple[float, float]] = {}

    device_nodes = [n for n in nodes if n.get("node_type") == "device"]
    if device_nodes:
        total_h = _NODE_V_GAP * (len(device_nodes) - 1)
        start_y = center_y - total_h / 2
        device_y = [start_y + _NODE_V_GAP * i for i in range(len(device_nodes))]
    else:
        device_y = []

    device_index = 0
    printer_index = 0
    for node in nodes:
        node_id = str(node.get("id", ""))
        node_type = node.get("node_type")
        if node_type == "pc":
            positions[node_id] = (110, center_y)
        elif node_type == "gateway":
            positions[node_id] = (110 + _COL_W, center_y)
        elif node_type == "device":
            positions[node_id] = (110 + _COL_W * 2, device_y[device_index])
            device_index += 1
        elif node_type == "printer":
            positions[node_id] = (110, center_y + 120 + printer_index * _NODE_V_GAP)
            printer_index += 1

    return positions


# ── Graph scene helpers ───────────────────────────────────────────────────────

def _add_node(scene: QGraphicsScene, pos: tuple[float, float], node: dict) -> None:
    cx, cy = pos
    node_type = str(node.get("node_type", "device"))
    border_color = QColor(_NODE_COLORS.get(node_type, "#2e7d32"))
    bg_color     = QColor(_NODE_BG.get(node_type, "#0d2e1a"))
    icon         = _NODE_ICONS.get(node_type, "●")

    x = cx - _CARD_W / 2
    y = cy - _CARD_H / 2

    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, _CARD_W, _CARD_H), _RADIUS, _RADIUS)
    card = QGraphicsPathItem(path)
    card.setBrush(QBrush(bg_color))
    card.setPen(QPen(border_color, 2))
    card.setZValue(1)
    scene.addItem(card)

    icon_item = QGraphicsTextItem(icon)
    icon_item.setFont(QFont("Segoe UI Emoji", 16))
    icon_item.setDefaultTextColor(QColor("#1F2937"))
    icon_item.setPos(cx - icon_item.boundingRect().width() / 2, y + 6)
    icon_item.setZValue(2)
    scene.addItem(icon_item)

    label_item = QGraphicsTextItem(str(node.get("label", "")))
    label_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
    label_item.setDefaultTextColor(QColor("#1F2937"))
    label_item.setTextWidth(_CARD_W - 8)
    label_item.setPos(x + 6, y + 32)
    label_item.setZValue(2)
    scene.addItem(label_item)

    sub_text = str(node.get("sublabel", ""))
    if sub_text:
        sub_item = QGraphicsTextItem(sub_text)
        sub_item.setFont(QFont("Segoe UI", 7))
        sub_item.setDefaultTextColor(QColor("#6B7280"))
        sub_item.setTextWidth(_CARD_W - 12)
        sub_item.setPos(x + 6, y + 48)
        sub_item.setZValue(2)
        scene.addItem(sub_item)

    detail_lines = [
        f"OS: {node.get('os', 'Unknown')}",
        f"Confidence: {node.get('confidence', 'LOW')}",
        f"Detected by: {node.get('detected_by', '—')}",
    ]
    detail_item = QGraphicsTextItem("\n".join(detail_lines))
    detail_item.setFont(QFont("Segoe UI", 6))
    detail_item.setDefaultTextColor(QColor("#6B7280"))
    detail_item.setTextWidth(_CARD_W - 12)
    detail_item.setPos(x + 6, y + 66)
    detail_item.setZValue(2)
    scene.addItem(detail_item)


def _arrowhead(
    scene: QGraphicsScene,
    p1: tuple[float, float],
    p2: tuple[float, float],
    color: QColor,
    size: float = 9,
) -> None:
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    pull = _CARD_W / 2 + 2
    tip_x, tip_y = p2[0] - ux * pull, p2[1] - uy * pull
    poly = QPolygonF([
        QPointF(tip_x, tip_y),
        QPointF(tip_x - ux * size + px * size * 0.45,
                tip_y - uy * size + py * size * 0.45),
        QPointF(tip_x - ux * size - px * size * 0.45,
                tip_y - uy * size - py * size * 0.45),
    ])
    item = QGraphicsPolygonItem(poly)
    item.setBrush(QBrush(color))
    item.setPen(QPen(Qt.PenStyle.NoPen))
    item.setZValue(1)
    scene.addItem(item)


def _add_edge(
    scene: QGraphicsScene,
    p1: tuple[float, float],
    p2: tuple[float, float],
    dashed: bool = False,
    color: str = "#2d5480",
    arrow: bool = True,
) -> None:
    qcolor = QColor(color)
    pen = QPen(qcolor, 2)
    if dashed:
        pen.setStyle(Qt.PenStyle.DashLine)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    scene.addLine(p1[0], p1[1], p2[0], p2[1], pen)
    if arrow:
        _arrowhead(scene, p1, p2, qcolor)


# ── Map view ──────────────────────────────────────────────────────────────────

class _TopologyView(QGraphicsView):
    _ZOOM_IN  = 1.15
    _ZOOM_OUT = 1 / 1.15

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("background: #06111b; border: none;")
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = self._ZOOM_IN if event.angleDelta().y() > 0 else self._ZOOM_OUT
        self.scale(factor, factor)


def _legend_pill(label: str, color: str) -> QFrame:
    pill = QFrame()
    pill.setStyleSheet(
        f"background-color: transparent; border: 1px solid {color};"
        f" border-radius: 10px; padding: 2px 8px;"
    )
    row = QHBoxLayout(pill)
    row.setContentsMargins(6, 2, 8, 2)
    row.setSpacing(4)
    dot = QLabel("●")
    dot.setStyleSheet(f"color: {color}; border: none; font-size: 9px;")
    text = QLabel(label)
    text.setStyleSheet(f"color: {color}; border: none; font-size: 11px;")
    row.addWidget(dot)
    row.addWidget(text)
    return pill


# ── Inventory view helpers ────────────────────────────────────────────────────

def _badge(text: str, fg: str, bg: str = "") -> QLabel:
    lbl = QLabel(text)
    bg_part = f"background: {bg};" if bg else "background: transparent;"
    lbl.setStyleSheet(
        f"color: {fg}; {bg_part} border: 1px solid {fg};"
        f" border-radius: 4px; padding: 1px 7px; font-size: 11px; font-weight: 600;"
    )
    return lbl


def _section_label(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setStyleSheet(
        "color: #6B7280; font-size: 11px; font-weight: bold;"
        " padding: 12px 0 4px 0; letter-spacing: 0.5px;"
    )
    return lbl


def _filter_btn(label: str) -> QPushButton:
    btn = QPushButton(label)
    btn.setCheckable(True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        "QPushButton { background: transparent; border: 1px solid #30363d;"
        " border-radius: 12px; padding: 3px 12px; font-size: 11px; color: #6B7280; }"
        "QPushButton:checked { border-color: #58a6ff; color: #58a6ff; background: #0a1929; }"
        "QPushButton:hover:!checked { border-color: #6B7280; color: #6B7280; }"
    )
    return btn


def _is_noise_arp(entry: ArpEntry) -> bool:
    """True for multicast/broadcast ARP entries that are network noise."""
    ip  = entry.ip_address or ""
    mac = (entry.mac_address or "").upper().replace(":", "-")
    if ":" in ip:
        return False
    try:
        first, last = int(ip.split(".")[0]), int(ip.split(".")[-1])
    except (ValueError, IndexError):
        return False
    if first >= 224 or last in (0, 255):
        return True
    return mac.startswith("01-00-5E") or mac == "FF-FF-FF-FF-FF-FF"


class _StatCard(QFrame):
    def __init__(self, icon: str, title: str, value: str, sub: str, color: str) -> None:
        super().__init__()
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"QFrame {{ background: transparent; border: 1px solid {color};"
            f" border-radius: 6px; }}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 5, 10, 4)
        lay.setSpacing(2)

        top = QHBoxLayout()
        top.setSpacing(4)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"border: none; color: {color}; font-size: 11px;")
        top_lbl = QLabel(title)
        top_lbl.setStyleSheet(f"border: none; color: {color}; font-size: 9px; font-weight: bold;")
        top.addWidget(icon_lbl)
        top.addWidget(top_lbl)
        top.addStretch(1)
        self._val = QLabel(value)
        self._val.setStyleSheet("border: none; color: #f0f6fc; font-size: 13px; font-weight: 800;")
        top.addWidget(self._val)
        lay.addLayout(top)

        self._sub = QLabel(sub)
        self._sub.setStyleSheet("border: none; color: #6B7280; font-size: 9px;")
        lay.addWidget(self._sub)

    def set_value(self, value: str, sub: str = "") -> None:
        self._val.setText(value)
        if sub:
            self._sub.setText(sub)


# Windows Get-NetNeighbor State enum values
_ARP_STATE = {"2": "Reachable", "4": "Stale", "6": "Unreachable", "8": "Incomplete"}


_TYPE_ICONS = {"pc": "🖥", "printer": "🖨", "web_device": "🌐", "unknown": "💻"}
_TYPE_COLORS = {"pc": "#1f6feb", "printer": "#a371f7", "web_device": "#58a6ff", "unknown": "#6B7280"}


class _DeviceRow(QFrame):
    """One discovered host (non-printer) from active subnet scan."""

    def __init__(self, dev: DiscoveredDevice) -> None:
        super().__init__()
        self.setObjectName("StatusCard")
        self.setFixedHeight(56)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(12)

        icon = QLabel(_TYPE_ICONS.get(dev.device_type, "💻"))
        icon.setStyleSheet("font-size: 18px;")
        icon.setFixedWidth(28)
        row.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(1)
        name = dev.hostname or dev.ip_address
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #f0f6fc;")
        info.addWidget(name_lbl)
        sub_parts = [p for p in (dev.ip_address if dev.hostname else "", dev.mac_address) if p]
        sub_lbl = QLabel("  ·  ".join(sub_parts) or dev.ip_address)
        sub_lbl.setStyleSheet("color: #6B7280; font-size: 11px; font-family: monospace;")
        info.addWidget(sub_lbl)
        row.addLayout(info, stretch=1)

        color = _TYPE_COLORS.get(dev.device_type, "#6B7280")
        type_label = dev.device_type.replace("_", " ").title() if dev.device_type != "unknown" else "Unknown"
        row.addWidget(_badge(type_label, color))

        if dev.confidence == "HIGH":
            row.addWidget(_badge(dev.confidence, "#3fb950"))


class _PrinterRow(QFrame):
    """One printer — from local Windows inventory or from active network scan."""

    def __init__(
        self,
        name: str,
        ip: str,
        sub: str,
        status: str = "",
        is_default: bool = False,
        network: bool = False,
    ) -> None:
        super().__init__()
        self.setObjectName("StatusCard")
        self.setFixedHeight(56)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(12)

        icon = QLabel("🖨")
        icon.setStyleSheet("font-size: 18px;")
        icon.setFixedWidth(28)
        row.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #f0f6fc;")
        info.addWidget(name_lbl)
        sub_lbl = QLabel(sub or ip or "—")
        sub_lbl.setStyleSheet("color: #6B7280; font-size: 11px;")
        info.addWidget(sub_lbl)
        row.addLayout(info, stretch=1)

        if ip:
            ip_lbl = QLabel(ip)
            ip_lbl.setStyleSheet("color: #9aa4b2; font-size: 11px; font-family: monospace;")
            row.addWidget(ip_lbl)

        if status:
            sc = "#3fb950" if status in ("Normal", "Ready") else "#d29922"
            row.addWidget(_badge(status, sc))
        if is_default:
            row.addWidget(_badge("★ Default", "#d29922", "#1a1000"))
        if network:
            row.addWidget(_badge("Network", "#a371f7", "#1e0938"))


class _NoiseRow(QFrame):
    """One multicast/broadcast ARP entry — shown in Network noise filter."""

    def __init__(self, entry: ArpEntry) -> None:
        super().__init__()
        self.setObjectName("StatusCard")
        self.setFixedHeight(48)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(12)

        icon = QLabel("📡")
        icon.setStyleSheet("font-size: 15px;")
        icon.setFixedWidth(28)
        row.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(1)
        ip_lbl = QLabel(entry.ip_address)
        ip_lbl.setStyleSheet("font-size: 12px; color: #484f58; font-family: monospace;")
        info.addWidget(ip_lbl)
        mac_lbl = QLabel(entry.mac_address or "—")
        mac_lbl.setStyleSheet("color: #3d444d; font-size: 10px; font-family: monospace;")
        info.addWidget(mac_lbl)
        row.addLayout(info, stretch=1)

        row.addWidget(_badge("multicast/broadcast", "#484f58"))


class _InventoryView(QWidget):
    """Scrollable device + printer inventory — default tab."""

    _PLACEHOLDER = "Run a scan to see network devices."

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Summary row (compact cards)
        summary_row = QHBoxLayout()
        summary_row.setSpacing(8)
        summary_row.setContentsMargins(16, 10, 16, 4)

        self._card_pc       = _StatCard("🖥", "THIS PC",   "—", "—", "#1f6feb")
        self._card_gateway  = _StatCard("🌐", "GATEWAY",   "—", "—", "#e65100")
        self._card_devices  = _StatCard("💻", "DEVICES",   "0", "ARP table", "#2e7d32")
        self._card_printers = _StatCard("🖨", "PRINTERS",  "0", "Windows inventory", "#7b1fa2")
        for c in (self._card_pc, self._card_gateway, self._card_devices, self._card_printers):
            summary_row.addWidget(c)

        summary_wrapper = QWidget()
        summary_wrapper.setLayout(summary_row)
        outer.addWidget(summary_wrapper)

        # Filter bar
        filter_wrapper = QWidget()
        filter_row = QHBoxLayout(filter_wrapper)
        filter_row.setContentsMargins(16, 4, 16, 6)
        filter_row.setSpacing(6)

        self._btn_all      = _filter_btn("All")
        self._btn_printers = _filter_btn("Printers")
        self._btn_pcs      = _filter_btn("PCs")
        self._btn_unknown  = _filter_btn("Unknown")
        self._btn_noise    = _filter_btn("Network noise")

        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        for btn in (self._btn_all, self._btn_printers, self._btn_pcs,
                    self._btn_unknown, self._btn_noise):
            self._filter_group.addButton(btn)
            filter_row.addWidget(btn)
        self._btn_all.setChecked(True)
        filter_row.addStretch(1)

        outer.addWidget(filter_wrapper)

        # Scrollable content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(16, 0, 16, 16)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._placeholder = QLabel(self._PLACEHOLDER)
        self._placeholder.setStyleSheet("color: #6B7280; font-size: 13px; padding: 40px;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._placeholder)

        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll, stretch=1)

        # Stored scan data (populated by update_data, read by _apply_filter)
        self._local_printers: list[PrinterInfo] = []
        self._net_printers: list[DiscoveredDevice] = []
        self._devices: list[DiscoveredDevice] = []
        self._noise: list[ArpEntry] = []

        self._filter_group.buttonClicked.connect(lambda _: self._apply_filter())

    def update_data(
        self,
        network: NetworkData,
        printers: PrintersData,
        discovered: list[DiscoveredDevice] | None = None,
    ) -> None:
        local_ips = {ip.ip_address for ip in network.ip_addresses if ip.ip_address}
        local_ip  = next(iter(local_ips), "—")
        hostname  = network.hostname or "This PC"
        gateway_ip = network.gateways[0].next_hop if network.gateways else "—"
        gw_ok = network.gateway_reachable

        self._card_pc.set_value(hostname, local_ip)
        gw_sub = "Active" if gw_ok else ("Unreachable" if gw_ok is False else "Unknown")
        self._card_gateway.set_value(gateway_ip, gw_sub)

        _VIRTUAL = ("PORTPROMPT:", "SHRFAX:", "NUL:")
        self._local_printers = [
            p for p in printers.printers
            if p.name and not any(p.port_name.startswith(v) for v in _VIRTUAL)
        ]
        local_printer_ips = {p.ip_address for p in self._local_printers if p.ip_address}

        if discovered is not None:
            self._net_printers = [
                d for d in discovered
                if d.device_type == "printer" and d.ip_address not in local_printer_ips
            ]
            self._devices = [
                d for d in discovered
                if d.device_type != "printer"
                and d.ip_address != gateway_ip
                and d.ip_address not in local_ips
            ]
            scan_label = "active scan"
        else:
            self._net_printers = []
            self._devices = []
            scan_label = "ARP table"

        self._noise = [e for e in network.arp_entries if _is_noise_arp(e)]

        total_printers = len(self._local_printers) + len(self._net_printers)
        self._card_printers.set_value(str(total_printers), "Windows inventory")
        self._card_devices.set_value(str(len(self._devices)), scan_label)

        self._apply_filter()

    def _apply_filter(self) -> None:
        checked = self._filter_group.checkedButton()
        if   checked is self._btn_printers: filt = "printers"
        elif checked is self._btn_pcs:      filt = "pcs"
        elif checked is self._btn_unknown:  filt = "unknown"
        elif checked is self._btn_noise:    filt = "noise"
        else:                               filt = "all"

        while self._layout.count():
            item = self._layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        if filt == "noise":
            self._render_noise()
            return

        show_printers = filt in ("all", "printers")
        all_printers  = self._local_printers if show_printers else []
        net_printers  = self._net_printers   if show_printers else []

        if   filt == "pcs":     devices = [d for d in self._devices if d.device_type == "pc"]
        elif filt == "unknown": devices = [d for d in self._devices if d.device_type == "unknown"]
        elif filt == "all":     devices = self._devices
        else:                   devices = []

        if not all_printers and not net_printers and not devices:
            if not (self._local_printers or self._net_printers or self._devices):
                self._layout.addWidget(self._placeholder)
            else:
                lbl = QLabel("No devices match the selected filter.")
                lbl.setStyleSheet("color: #6B7280; font-size: 13px; padding: 40px;")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._layout.addWidget(lbl)
            return

        total_p = len(all_printers) + len(net_printers)
        if all_printers or net_printers:
            self._layout.addWidget(_section_label(f"PRINTERS  ({total_p})"))
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #21262d;")
            self._layout.addWidget(sep)
            for p in all_printers:
                self._layout.addWidget(_PrinterRow(
                    name=p.name, ip=p.ip_address,
                    sub=p.ip_address or p.port_name or "Local port",
                    status=p.status or "Normal",
                    is_default=p.is_default,
                    network=bool(p.ip_address),
                ))
            for d in net_printers:
                self._layout.addWidget(_PrinterRow(
                    name=d.hostname or d.ip_address,
                    ip=d.ip_address,
                    sub=f"Detected by: {d.detected_by}",
                    network=True,
                ))

        if devices:
            self._layout.addWidget(_section_label(f"DEVICES  ({len(devices)})"))
            sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
            sep2.setStyleSheet("color: #21262d;")
            self._layout.addWidget(sep2)
            for dev in devices:
                self._layout.addWidget(_DeviceRow(dev))

        if filt == "all" and self._noise:
            noise_lbl = QLabel(
                f"📡  Hidden: {len(self._noise)} multicast/broadcast entries"
                f"  —  click \"Network noise\" to show"
            )
            noise_lbl.setStyleSheet("color: #484f58; font-size: 11px; padding: 8px 0 4px 0;")
            self._layout.addWidget(noise_lbl)

        self._layout.addStretch(1)

    def _render_noise(self) -> None:
        if not self._noise:
            lbl = QLabel("No multicast/broadcast entries detected.")
            lbl.setStyleSheet("color: #6B7280; font-size: 13px; padding: 40px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(lbl)
            return
        self._layout.addWidget(_section_label(f"NETWORK NOISE  ({len(self._noise)})"))
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #21262d;")
        self._layout.addWidget(sep)
        for entry in self._noise:
            self._layout.addWidget(_NoiseRow(entry))
        self._layout.addStretch(1)


# ── Main page ─────────────────────────────────────────────────────────────────

class TopologyPage(QWidget):
    """Network topology — Inventory (default) and Map tabs."""

    def __init__(self) -> None:
        super().__init__()
        self._network: NetworkData | None = None
        self._printers: PrintersData | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("PanelCard")
        header.setStyleSheet(
            "QFrame#PanelCard { border-radius: 0; border-left: none;"
            " border-right: none; border-top: none; }"
        )
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(16, 10, 16, 10)

        title = QLabel("🗺 Network Topology")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_row.addWidget(title)
        h_row.addStretch(1)

        self._status_label = QLabel("Not scanned")
        self._status_label.setStyleSheet("color: #9aa4b2;")
        h_row.addWidget(self._status_label)
        h_row.addSpacing(12)

        self._scan_btn = QPushButton("▶ Scan Network")
        self._scan_btn.clicked.connect(self._run_scan)
        h_row.addWidget(self._scan_btn)
        outer.addWidget(header)

        # ── Tab bar ───────────────────────────────────────────────────────────
        tab_bar = QFrame()
        tab_bar.setStyleSheet(
            "QFrame { background: #0d1117; border-bottom: 1px solid #21262d; }"
        )
        tab_row = QHBoxLayout(tab_bar)
        tab_row.setContentsMargins(16, 0, 16, 0)
        tab_row.setSpacing(0)

        self._tab_inventory = self._make_tab("📋  Inventory", 0)
        self._tab_map       = self._make_tab("🗺  Map", 1)
        tab_row.addWidget(self._tab_inventory)
        tab_row.addWidget(self._tab_map)
        tab_row.addStretch(1)

        self._fit_btn = QPushButton("⊡ Fit")
        self._fit_btn.setToolTip("Reset zoom and pan")
        self._fit_btn.clicked.connect(self._fit_view)
        self._fit_btn.setVisible(False)
        tab_row.addWidget(self._fit_btn)

        outer.addWidget(tab_bar)

        # ── Stacked views ─────────────────────────────────────────────────────
        self._stack = QStackedWidget()

        # Page 0: Inventory
        self._inventory = _InventoryView()
        self._stack.addWidget(self._inventory)

        # Page 1: Map (graph)
        map_page = QWidget()
        map_layout = QVBoxLayout(map_page)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(0)

        self._scene = QGraphicsScene()
        self._view = _TopologyView(self._scene)
        map_layout.addWidget(self._view, stretch=1)

        legend = QFrame()
        legend.setObjectName("PanelCard")
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(16, 8, 16, 8)
        legend_layout.setSpacing(8)
        for node_type, label in [
            ("pc", "This PC"), ("gateway", "Gateway"),
            ("device", "Device"), ("printer", "Printer"),
        ]:
            legend_layout.addWidget(_legend_pill(label, _NODE_COLORS[node_type]))
        hint = QLabel("Scroll: zoom  ·  Drag: pan  ·  ⊡ Fit: reset view")
        hint.setStyleSheet("color: #4b5566; font-size: 11px;")
        legend_layout.addStretch(1)
        legend_layout.addWidget(hint)
        map_layout.addWidget(legend)

        self._stack.addWidget(map_page)
        outer.addWidget(self._stack, stretch=1)

        self._switch_tab(0)
        self._draw_topology(NetworkData(), PrintersData())

    def _make_tab(self, label: str, index: int) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setStyleSheet(
            "QPushButton { background: transparent; color: #6B7280; border: none;"
            " border-bottom: 2px solid transparent; padding: 8px 16px;"
            " font-size: 13px; }"
            "QPushButton:checked { color: #f0f6fc; border-bottom: 2px solid #58a6ff; }"
            "QPushButton:hover:!checked { color: #6B7280; }"
        )
        btn.clicked.connect(lambda: self._switch_tab(index))
        return btn

    def _switch_tab(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._tab_inventory.setChecked(index == 0)
        self._tab_map.setChecked(index == 1)
        self._fit_btn.setVisible(index == 1)

    def load_data(self, network: NetworkData, printers: PrintersData, scanned_at: str = "") -> None:
        """Populate from shared Dashboard scan — no subnet discovery (click Scan Network for that)."""
        self._network = network
        self._printers = printers
        self._inventory.update_data(network, printers, None)
        self._draw_topology(network, printers)
        ts = scanned_at[11:19] if len(scanned_at) >= 19 else ""
        self._status_label.setText(
            f"From Dashboard scan{f'  {ts}' if ts else ''}  ·  Scan Network for full subnet discovery"
        )
        self._status_label.setStyleSheet("color: #9aa4b2;")

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setStyleSheet("color: #d29922;")
        QApplication.processEvents()

        runner = PowerShellRunner()

        self._status_label.setText("Scanning local network info…")
        QApplication.processEvents()
        network  = NetworkScanner(runner).scan()
        printers = PrintersScanner(runner).scan()

        def _prog(msg: str) -> None:
            self._status_label.setText(msg)
            QApplication.processEvents()

        self._status_label.setText("Active subnet scan — pinging all hosts…")
        QApplication.processEvents()
        discovered = SubnetScanner(runner).scan(on_progress=_prog)

        self._network  = network
        self._printers = printers

        self._inventory.update_data(network, printers, discovered)
        self._draw_topology(network, printers)

        printers_found = sum(1 for d in discovered if d.device_type == "printer")
        devices_found  = sum(1 for d in discovered if d.device_type != "printer")
        self._status_label.setText(
            f"{devices_found} device(s) · {printers_found} printer(s) found on subnet"
        )
        self._status_label.setStyleSheet("color: #3fb950;")
        self._scan_btn.setEnabled(True)

    # ── Map helpers ───────────────────────────────────────────────────────────

    def _fit_view(self) -> None:
        rect = self._scene.itemsBoundingRect()
        if not rect.isEmpty():
            self._view.fitInView(
                rect.adjusted(-40, -40, 40, 40),
                Qt.AspectRatioMode.KeepAspectRatio,
            )

    def _draw_topology(self, network: NetworkData, printers: PrintersData) -> None:
        self._scene.clear()

        nodes = build_nodes(network, printers)
        device_nodes = [n for n in nodes if n["node_type"] == "device"]

        canvas_w = max(800, self._view.viewport().width())
        canvas_h = max(500,
                       (len(device_nodes) + 2) * _NODE_V_GAP,
                       self._view.viewport().height())
        self._scene.setSceneRect(0, 0, canvas_w, canvas_h)

        positions = compute_positions(nodes, canvas_w, canvas_h)
        node_by_id = {str(n["id"]): n for n in nodes}

        if "pc" in positions and "gw" in positions:
            _add_edge(self._scene, positions["pc"], positions["gw"], color="#2d5480")

        if "gw" in positions:
            for node in nodes:
                if node.get("node_type") == "device":
                    _add_edge(self._scene, positions["gw"],
                              positions[str(node["id"])], dashed=True, color="#1a3d26")

        for node in nodes:
            if node.get("node_type") == "printer" and "pc" in positions:
                _add_edge(self._scene, positions["pc"],
                          positions[str(node["id"])], dashed=True, color="#3b1a5e")

        for node_id, pos in positions.items():
            _add_node(self._scene, pos, node_by_id[node_id])

        self._fit_view()
