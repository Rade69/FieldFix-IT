from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.modules.network.models import NetworkData
from app.modules.network.scanner import NetworkScanner, _format_speed


def _kv_row(key: str, value: str, value_color: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    key_label = QLabel(key)
    key_label.setStyleSheet("color: #9aa4b2; min-width: 200px;")
    key_label.setAlignment(Qt.AlignmentFlag.AlignTop)
    row.addWidget(key_label)
    val_label = QLabel(value)
    val_label.setWordWrap(True)
    val_label.setStyleSheet(f"color: {value_color}; font-weight: bold;" if value_color else "font-weight: bold;")
    row.addWidget(val_label, stretch=1)
    return row


def _panel(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("PanelCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(6)
    title_label = QLabel(title)
    title_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
    layout.addWidget(title_label)
    return frame, layout


class NetworkPage(QWidget):
    """Network diagnostics page. Scan triggered by button — synchronous for MVP."""

    def __init__(self) -> None:
        super().__init__()
        self._scanner = NetworkScanner(PowerShellRunner())
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header bar ─────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("PanelCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("🌐 Network Diagnostics")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        self._status_label = QLabel("Not scanned")
        self._status_label.setStyleSheet("color: #9aa4b2;")
        header_layout.addWidget(self._status_label)
        header_layout.addSpacing(12)

        self._scan_btn = QPushButton("▶ Run Scan")
        self._scan_btn.clicked.connect(self._run_scan)
        header_layout.addWidget(self._scan_btn)

        outer.addWidget(header)

        # ── Scrollable results area ─────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._results_widget = QWidget()
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._results_layout.setSpacing(8)
        self._results_layout.setContentsMargins(0, 8, 0, 8)

        placeholder = QLabel("  Click '▶ Run Scan' to collect network information.")
        placeholder.setStyleSheet("color: #9aa4b2; padding: 24px;")
        self._results_layout.addWidget(placeholder)

        scroll.setWidget(self._results_widget)
        outer.addWidget(scroll, stretch=1)

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setText("Scanning…")
        self._status_label.setStyleSheet("color: #d29922;")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        data = self._scanner.scan()
        self._display_results(data)

        self._scan_btn.setEnabled(True)
        self._status_label.setText(f"Done in {data.scan_duration_ms / 1000:.1f}s")
        self._status_label.setStyleSheet("color: #3fb950;")

    def _clear_results(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _display_results(self, data: NetworkData) -> None:
        self._clear_results()

        # Host / profile ─────────────────────────────────────────────────────
        frame, layout = _panel("💻 Host")
        layout.addLayout(_kv_row("Hostname", data.hostname or "—"))
        for p in data.profiles:
            color = "#3fb950" if p.category == "Private" else "#d29922"
            layout.addLayout(_kv_row(f"Profile ({p.interface_alias})", f"{p.name}  [{p.category}]", color))
        self._results_layout.addWidget(frame)

        # Active adapters ────────────────────────────────────────────────────
        if data.adapters:
            frame, layout = _panel(f"🔌 Active Adapters ({len(data.adapters)})")
            for a in data.adapters:
                speed_str = _format_speed(a.link_speed_bps) or "—"
                layout.addLayout(_kv_row(a.name, f"{a.description}  |  {speed_str}  |  {a.mac_address or '—'}"))
            self._results_layout.addWidget(frame)

        # IP / Gateway / DNS ─────────────────────────────────────────────────
        net_rows: list[tuple[str, str, str]] = []
        for ip in data.ip_addresses:
            net_rows.append((f"IP ({ip.interface_alias})", f"{ip.ip_address}/{ip.prefix_length or '?'}", ""))
        for gw in data.gateways:
            net_rows.append((f"Gateway ({gw.interface_alias})", gw.next_hop, ""))
        for d in data.dns:
            net_rows.append((f"DNS ({d.interface_alias})", ", ".join(d.servers), ""))
        if net_rows:
            frame, layout = _panel("📡 Addressing")
            for key, val, color in net_rows:
                layout.addLayout(_kv_row(key, val, color))
            self._results_layout.addWidget(frame)

        # Gateway ping ────────────────────────────────────────────────────────
        if data.gateway_reachable is not None:
            gw_ip = data.gateways[0].next_hop if data.gateways else "?"
            ok = data.gateway_reachable
            frame, layout = _panel("📶 Gateway Reachability")
            layout.addLayout(_kv_row(
                gw_ip,
                "✓ Reachable" if ok else "✕ Unreachable",
                "#3fb950" if ok else "#f85149",
            ))
            self._results_layout.addWidget(frame)

        # ARP table ───────────────────────────────────────────────────────────
        if data.arp_entries:
            shown = data.arp_entries[:25]
            frame, layout = _panel(f"🗂 ARP Table ({len(data.arp_entries)} entries)")
            for e in shown:
                layout.addLayout(_kv_row(e.ip_address, f"{e.mac_address}  |  {e.state}  |  {e.interface_alias}"))
            if len(data.arp_entries) > 25:
                more = QLabel(f"  … and {len(data.arp_entries) - 25} more entries")
                more.setStyleSheet("color: #9aa4b2;")
                layout.addWidget(more)
            self._results_layout.addWidget(frame)

        # Errors ──────────────────────────────────────────────────────────────
        if data.errors:
            frame, layout = _panel(f"⚠ Scan Warnings ({len(data.errors)})")
            for i, e in enumerate(data.errors, 1):
                layout.addLayout(_kv_row(f"#{i}", e, "#d29922"))
            self._results_layout.addWidget(frame)

        self._results_layout.addStretch(1)
