from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsEllipseItem,
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
from app.modules.network.models import NetworkData
from app.modules.network.scanner import NetworkScanner
from app.modules.printers.models import PrintersData
from app.modules.printers.scanner import PrintersScanner

_NODE_COLORS = {
    "pc": "#1f6feb",
    "gateway": "#e65100",
    "device": "#2e7d32",
    "printer": "#7b1fa2",
}

_RADIUS = 32


def build_nodes(network: NetworkData, printers: PrintersData) -> list[dict]:
    """Builds topology node list from scan data."""
    local_ips = {ip.ip_address for ip in network.ip_addresses if ip.ip_address}
    local_ip = next(iter(local_ips), "")
    gateway_ip = network.gateways[0].next_hop if network.gateways else ""

    nodes = [{
        "id": "pc",
        "label": network.hostname or "This PC",
        "sublabel": local_ip,
        "node_type": "pc",
    }]

    if gateway_ip:
        nodes.append({
            "id": "gw",
            "label": "Gateway",
            "sublabel": gateway_ip,
            "node_type": "gateway",
        })

    for entry in network.arp_entries:
        if not entry.ip_address:
            continue
        if entry.ip_address == gateway_ip or entry.ip_address in local_ips:
            continue
        nodes.append({
            "id": f"arp_{entry.ip_address}",
            "label": entry.ip_address,
            "sublabel": entry.mac_address,
            "node_type": "device",
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
    """Returns {node_id: (x, y)} without Qt dependencies."""
    del canvas_w
    center_y = canvas_h / 2
    positions: dict[str, tuple[float, float]] = {}

    device_nodes = [n for n in nodes if n.get("node_type") == "device"]
    printer_index = 0

    if device_nodes:
        natural_gap = canvas_h / (len(device_nodes) + 1)
        gap = max(70.0, natural_gap)
        if natural_gap >= 70:
            device_y = [gap * (i + 1) for i in range(len(device_nodes))]
        else:
            start_y = center_y - (gap * (len(device_nodes) - 1) / 2)
            device_y = [start_y + gap * i for i in range(len(device_nodes))]
    else:
        device_y = []

    device_index = 0
    for node in nodes:
        node_id = str(node.get("id", ""))
        node_type = node.get("node_type")
        if node_type == "pc":
            positions[node_id] = (110, center_y)
        elif node_type == "gateway":
            positions[node_id] = (310, center_y)
        elif node_type == "device":
            positions[node_id] = (510, device_y[device_index])
            device_index += 1
        elif node_type == "printer":
            positions[node_id] = (110, center_y + 120 + printer_index * 80)
            printer_index += 1

    return positions


class TopologyPage(QWidget):
    """Network topology page. Draws PC, gateway, ARP devices and network printers."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

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

        self._scan_btn = QPushButton("▶ Scan")
        self._scan_btn.clicked.connect(self._run_scan)
        header_layout.addWidget(self._scan_btn)

        outer.addWidget(header)

        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setStyleSheet("background: #0d1117; border: none;")
        self._view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._view.setMinimumHeight(420)
        outer.addWidget(self._view, stretch=1)

        legend = QFrame()
        legend.setObjectName("PanelCard")
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(16, 8, 16, 8)
        for node_type, label in [
            ("pc", "This PC"),
            ("gateway", "Gateway"),
            ("device", "Device"),
            ("printer", "Printer"),
        ]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {_NODE_COLORS[node_type]};")
            text = QLabel(label)
            text.setStyleSheet("color: #9aa4b2;")
            legend_layout.addWidget(dot)
            legend_layout.addWidget(text)
            legend_layout.addSpacing(16)
        legend_layout.addStretch(1)
        outer.addWidget(legend)

        self._draw_topology(NetworkData(), PrintersData())

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setText("Scanning…")
        self._status_label.setStyleSheet("color: #d29922;")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        network = NetworkScanner(PowerShellRunner()).scan()
        printers = PrintersScanner(PowerShellRunner()).scan()

        self._draw_topology(network, printers)

        total = len(network.arp_entries)
        self._scan_btn.setEnabled(True)
        self._status_label.setText(f"Done — {total} device(s) found")
        self._status_label.setStyleSheet("color: #3fb950;")

    def _draw_topology(self, network: NetworkData, printers: PrintersData) -> None:
        self._scene.clear()
        canvas_w = max(760, self._view.viewport().width())
        canvas_h = max(420, self._view.viewport().height())
        self._scene.setSceneRect(0, 0, canvas_w, canvas_h)

        nodes = build_nodes(network, printers)
        positions = compute_positions(nodes, canvas_w, canvas_h)
        node_by_id = {str(node["id"]): node for node in nodes}

        if "pc" in positions and "gw" in positions:
            self._add_edge(self._scene, positions["pc"], positions["gw"])

        if "gw" in positions:
            for node in nodes:
                if node.get("node_type") == "device":
                    self._add_edge(self._scene, positions["gw"], positions[str(node["id"])], dashed=True)

        for node in nodes:
            if node.get("node_type") == "printer" and "pc" in positions:
                self._add_edge(
                    self._scene,
                    positions["pc"],
                    positions[str(node["id"])],
                    dashed=True,
                    color="#7b1fa2",
                )

        for node_id, pos in positions.items():
            self._add_node(self._scene, pos, node_by_id[node_id])

    def _add_node(self, scene: QGraphicsScene, pos: tuple[float, float], node_dict: dict) -> None:
        x, y = pos
        node_type = str(node_dict.get("node_type", "device"))
        color = QColor(_NODE_COLORS.get(node_type, "#2e7d32"))

        circle = QGraphicsEllipseItem(QRectF(x - _RADIUS, y - _RADIUS, _RADIUS * 2, _RADIUS * 2))
        circle.setBrush(QBrush(color))
        circle.setPen(QPen(QColor("#ffffff"), 2))
        scene.addItem(circle)

        label = QGraphicsTextItem(str(node_dict.get("label", "")))
        label.setDefaultTextColor(QColor("#f0f6fc"))
        label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        label.setTextWidth(150)
        label.setPos(x - 75, y + _RADIUS + 6)
        scene.addItem(label)

        sublabel = QGraphicsTextItem(str(node_dict.get("sublabel", "")))
        sublabel.setDefaultTextColor(QColor("#9aa4b2"))
        sublabel.setFont(QFont("Segoe UI", 8))
        sublabel.setTextWidth(150)
        sublabel.setPos(x - 75, y + _RADIUS + 20)
        scene.addItem(sublabel)

    def _add_edge(
        self,
        scene: QGraphicsScene,
        p1: tuple[float, float],
        p2: tuple[float, float],
        dashed: bool = False,
        color: str = "#9aa4b2",
    ) -> None:
        pen = QPen(QColor(color), 2)
        if dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        scene.addLine(p1[0], p1[1], p2[0], p2[1], pen)
