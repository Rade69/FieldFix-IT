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
    QFrame,
    QGraphicsPathItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.modules.network.models import NetworkData, OsFingerprint
from app.modules.network.scanner import NetworkScanner
from app.modules.printers.models import PrintersData
from app.modules.printers.scanner import PrintersScanner

# ── node palette ──────────────────────────────────────────────────────────────
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

_CARD_W  = 170
_CARD_H  = 124
_RADIUS  = 8       # rounded corner radius
_NODE_V_GAP = 136
_COL_W  = 280


# ── pure layout logic (no Qt widgets — testable) ──────────────────────────────

def build_nodes(network: NetworkData, printers: PrintersData) -> list[dict]:
    """Builds topology node list from scan data. IPv6 entries are excluded."""
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
        if not entry.ip_address:
            continue
        if ":" in entry.ip_address:
            continue
        if entry.ip_address == gateway_ip or entry.ip_address in local_ips:
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
        if printer.printer_type != "Connection" and not printer.is_default:
            continue
        nodes.append({
            "id": f"printer_{printer_count}",
            "label": printer.name[:14] if printer.name else "Printer",
            "sublabel": "★ Default" if printer.is_default else (printer.printer_type or "Printer"),
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
    """Returns {node_id: (cx, cy)} — center of each card."""
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


# ── graphics scene helpers ────────────────────────────────────────────────────

def _add_node(scene: QGraphicsScene, pos: tuple[float, float], node: dict) -> None:
    cx, cy = pos
    node_type = str(node.get("node_type", "device"))
    border_color = QColor(_NODE_COLORS.get(node_type, "#2e7d32"))
    bg_color     = QColor(_NODE_BG.get(node_type, "#0d2e1a"))
    icon         = _NODE_ICONS.get(node_type, "●")

    x = cx - _CARD_W / 2
    y = cy - _CARD_H / 2

    # Card background (rounded rect)
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, _CARD_W, _CARD_H), _RADIUS, _RADIUS)
    card = QGraphicsPathItem(path)
    card.setBrush(QBrush(bg_color))
    pen = QPen(border_color, 2)
    card.setPen(pen)
    card.setZValue(1)
    scene.addItem(card)

    # Icon (centered top)
    icon_item = QGraphicsTextItem(icon)
    icon_item.setFont(QFont("Segoe UI Emoji", 16))
    icon_item.setDefaultTextColor(QColor("#f0f6fc"))
    icon_w = icon_item.boundingRect().width()
    icon_item.setPos(cx - icon_w / 2, y + 6)
    icon_item.setZValue(2)
    scene.addItem(icon_item)

    # Label (name)
    label_text = str(node.get("label", ""))
    label_item = QGraphicsTextItem(label_text)
    label_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
    label_item.setDefaultTextColor(QColor("#f0f6fc"))
    label_item.setTextWidth(_CARD_W - 8)
    label_item.setPos(x + 6, y + 32)
    label_item.setZValue(2)
    scene.addItem(label_item)

    # Sublabel (IP / mac)
    sub_text = str(node.get("sublabel", ""))
    if sub_text:
        sub_item = QGraphicsTextItem(sub_text)
        sub_item.setFont(QFont("Segoe UI", 7))
        sub_item.setDefaultTextColor(QColor("#9aa4b2"))
        sub_item.setTextWidth(_CARD_W - 12)
        sub_item.setPos(x + 6, y + 48)
        sub_item.setZValue(2)
        scene.addItem(sub_item)

    detail_lines = [
        f"OS: {node.get('os', 'Unknown')}",
        f"Confidence: {node.get('confidence', 'LOW')}",
        f"Detected by: {node.get('detected_by', 'insufficient signals')}",
    ]
    detail_item = QGraphicsTextItem("\n".join(detail_lines))
    detail_item.setFont(QFont("Segoe UI", 6))
    detail_item.setDefaultTextColor(QColor("#c9d1d9"))
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
    """Draw a small filled triangle arrowhead pointing from p1 toward p2."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    ux, uy = dx / length, dy / length   # unit vector toward p2
    px, py = -uy, ux                    # perpendicular

    # Place tip at edge of destination card (pull back by half card)
    pull = _CARD_W / 2 + 2
    tip_x = p2[0] - ux * pull
    tip_y = p2[1] - uy * pull

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


# ── interactive view ──────────────────────────────────────────────────────────

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
        self.setMinimumHeight(420)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = self._ZOOM_IN if event.angleDelta().y() > 0 else self._ZOOM_OUT
        self.scale(factor, factor)


# ── legend helpers ────────────────────────────────────────────────────────────

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


# ── main page ─────────────────────────────────────────────────────────────────

class TopologyPage(QWidget):
    """Network topology page — card-style nodes, arrowhead edges, pill legend."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # Header
        header = QFrame()
        header.setObjectName("PanelCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("🗺 Network Topology")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        self._status_label = QLabel("Not scanned")
        self._status_label.setStyleSheet("color: #9aa4b2;")
        header_layout.addWidget(self._status_label)
        header_layout.addSpacing(12)

        self._fit_btn = QPushButton("⊡ Fit")
        self._fit_btn.setToolTip("Reset zoom and pan to show all devices")
        self._fit_btn.clicked.connect(self._fit_view)
        header_layout.addWidget(self._fit_btn)
        header_layout.addSpacing(6)

        self._scan_btn = QPushButton("▶ Scan")
        self._scan_btn.clicked.connect(self._run_scan)
        header_layout.addWidget(self._scan_btn)

        outer.addWidget(header)

        # Scene + view
        self._scene = QGraphicsScene()
        self._view = _TopologyView(self._scene)
        outer.addWidget(self._view, stretch=1)

        # Legend (pill badges)
        legend = QFrame()
        legend.setObjectName("PanelCard")
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(16, 8, 16, 8)
        legend_layout.setSpacing(8)
        for node_type, label in [
            ("pc",      "This PC"),
            ("gateway", "Gateway"),
            ("device",  "Device"),
            ("printer", "Printer"),
        ]:
            legend_layout.addWidget(_legend_pill(label, _NODE_COLORS[node_type]))

        hint = QLabel("Scroll: zoom  ·  Drag: pan  ·  ⊡ Fit: reset view")
        hint.setStyleSheet("color: #4b5566; font-size: 11px;")
        legend_layout.addStretch(1)
        legend_layout.addWidget(hint)
        outer.addWidget(legend)

        self._draw_topology(NetworkData(), PrintersData())

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setText("Scanning…")
        self._status_label.setStyleSheet("color: #d29922;")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        runner = PowerShellRunner()
        network = NetworkScanner(runner).scan()
        printers = PrintersScanner(runner).scan()

        nodes = build_nodes(network, printers)
        self._draw_topology(network, printers)

        device_count = sum(1 for n in nodes if n["node_type"] == "device")
        self._scan_btn.setEnabled(True)
        self._status_label.setText(f"Done — {device_count} device(s) found")
        self._status_label.setStyleSheet("color: #3fb950;")

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
        canvas_h = max(500, (len(device_nodes) + 2) * _NODE_V_GAP,
                       self._view.viewport().height())
        self._scene.setSceneRect(0, 0, canvas_w, canvas_h)

        positions = compute_positions(nodes, canvas_w, canvas_h)
        node_by_id = {str(n["id"]): n for n in nodes}

        # Edges first (behind cards)
        if "pc" in positions and "gw" in positions:
            _add_edge(self._scene, positions["pc"], positions["gw"], color="#2d5480")

        if "gw" in positions:
            for node in nodes:
                if node.get("node_type") == "device":
                    _add_edge(
                        self._scene,
                        positions["gw"],
                        positions[str(node["id"])],
                        dashed=True,
                        color="#1a3d26",
                    )

        for node in nodes:
            if node.get("node_type") == "printer" and "pc" in positions:
                _add_edge(
                    self._scene,
                    positions["pc"],
                    positions[str(node["id"])],
                    dashed=True,
                    color="#3b1a5e",
                )

        # Cards on top
        for node_id, pos in positions.items():
            _add_node(self._scene, pos, node_by_id[node_id])

        self._fit_view()
