from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.reports.models import ScanReport

_STATUS_STYLE = {
    "ok":   ("✓", "#3fb950"),
    "fail": ("✕", "#f85149"),
    "info": ("●", "#a371f7"),
    "warn": ("⚠", "#d29922"),
}


def _row(label: str, value: str, status: str) -> QHBoxLayout:
    icon, color = _STATUS_STYLE.get(status, ("●", "#9aa4b2"))
    r = QHBoxLayout()
    r.addWidget(_styled(icon, f"color: {color}; font-weight: bold;"))
    r.addWidget(QLabel(label))
    r.addStretch(1)
    r.addWidget(_styled(value, f"color: {color}; font-weight: bold;"))
    return r


def _styled(text: str, style: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    return lbl


def _svc_status(services, name: str) -> tuple[str, str]:
    for s in services:
        if s.name == name:
            if s.status == "Running":
                return "Running", "ok"
            if s.status == "Stopped":
                return "Stopped", "fail"
            return s.status, "warn"
    return "Not found", "fail"


def _build_rows(report: ScanReport) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []

    net = report.network
    smb = report.smb
    svc = report.services
    prn = report.printers

    if net:
        if net.gateways:
            gw = net.gateways[0].next_hop
            if net.gateway_reachable is True:
                rows.append((f"Ping Gateway ({gw})", "OK", "ok"))
            elif net.gateway_reachable is False:
                rows.append((f"Ping Gateway ({gw})", "FAIL", "fail"))
            else:
                rows.append((f"Ping Gateway ({gw})", "—", "info"))
        else:
            rows.append(("No gateway configured", "—", "fail"))
    else:
        rows.append(("Network scan", "Not run", "info"))

    if smb and smb.port_445:
        p = smb.port_445
        val = "Open" if p.reachable else ("Closed" if p.reachable is False else "—")
        st = "ok" if p.reachable else ("fail" if p.reachable is False else "info")
        rows.append((f"SMB Port 445 ({p.target_ip})", val, st))

    if smb and smb.server_config:
        sc = smb.server_config
        if sc.smb1_enabled is True:
            rows.append(("SMB1 Protocol", "ENABLED (risk)", "fail"))
        elif sc.smb1_enabled is False:
            rows.append(("SMB1 Protocol", "Disabled ✓", "ok"))

    if svc:
        services_list = svc.services
        for svc_name, display in [
            ("LanmanServer", "Server Service"),
            ("LanmanWorkstation", "Workstation Service"),
            ("FDResPub", "FDResPub"),
            ("Spooler", "Print Spooler"),
        ]:
            val, st = _svc_status(services_list, svc_name)
            rows.append((display, val, st))
    else:
        rows.append(("Services scan", "Not run", "info"))

    if prn:
        count = len(prn.printers)
        rows.append(("Printers found", str(count), "info"))
    else:
        rows.append(("Printers scan", "Not run", "info"))

    return rows


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if w := item.widget():
            w.deleteLater()
        elif child := item.layout():
            _clear_layout(child)


class RecentScanWidget(QFrame):
    """Recent Scan Summary panel. Shows placeholder until update_data() is called."""

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
        header_row.addWidget(_styled("⟳", "color: #58a6ff;"))
        layout.addLayout(header_row)

        self._content = QVBoxLayout()
        layout.addLayout(self._content)

        self._footer = QLabel("Run a scan to see results.")
        self._footer.setStyleSheet("color: #9aa4b2; margin-top: 4px;")
        layout.addWidget(self._footer)

        self._show_placeholder()

    def _show_placeholder(self) -> None:
        _clear_layout(self._content)
        self._content.addLayout(_row("Gateway", "—", "info"))
        self._content.addLayout(_row("SMB Port 445", "—", "info"))
        self._content.addLayout(_row("Services", "—", "info"))

    def update_data(self, report: ScanReport) -> None:
        _clear_layout(self._content)
        for label, value, status in _build_rows(report):
            self._content.addLayout(_row(label, value, status))
        ts = report.generated_at.replace("T", " ")
        self._footer.setText(f"🕒 Last scan: {ts}")
