from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
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
from app.core.risk_level import RiskLevel
from app.core.settings import get_settings
from app.core.scan_session import ScanResult, ScanSession
from app.gui.widgets.decision_assistant_widget import DecisionAssistantWidget
from app.gui.widgets.issues_widget import IssuesRecommendationsWidget
from app.gui.widgets.quick_actions_widget import QuickActionsWidget
from app.gui.widgets.recent_scan_widget import RecentScanWidget
from app.gui.widgets.status_card import StatusCard
from app.gui.widgets.system_info_widget import SystemInfoWidget
from app.gui.widgets.timeline_widget import ActivityTimelineWidget, TimelineEvent
from app.gui.widgets.topology_widget import NetworkTopologyWidget


def _module_status(issues, module: str) -> str:
    """Derive ok/warning/critical from issues filtered by module."""
    relevant = [i for i in issues if i.related_module == module]
    if not relevant:
        return "ok"
    return "critical" if max(i.severity for i in relevant) >= RiskLevel.HIGH else "warning"


def _smb_detail(report) -> str:
    smb = report.smb
    if not smb:
        return "Not scanned"
    if smb.server_config:
        if smb.server_config.smb1_enabled is True:
            return "SMB1 active (risk)"
        if smb.server_config.smb1_enabled is False:
            return "SMB v2/v3 enabled"
    return "SMB config scanned"


def _services_detail(report) -> str:
    svc = report.services
    if not svc:
        return "Not scanned"
    total = len(svc.services)
    running = sum(1 for s in svc.services if s.status == "Running")
    return f"{running} / {total} running"


def _build_timeline_events(result: ScanResult) -> list[TimelineEvent]:
    ts = result.scanned_at[11:19]  # HH:MM:SS
    events: list[TimelineEvent] = []

    events.append(TimelineEvent(ts, "▶", "#58a6ff", "Full scan started", ""))

    net = result.report.network
    if net:
        gw_ok = net.gateway_reachable
        if gw_ok is True:
            events.append(TimelineEvent(ts, "✓", "#3fb950", "Network scan", "Gateway reachable"))
        elif gw_ok is False:
            events.append(TimelineEvent(ts, "✕", "#f85149", "Network scan", "Gateway unreachable"))
        else:
            events.append(TimelineEvent(ts, "✓", "#3fb950", "Network scan", f"{len(net.adapters)} adapter(s)"))

    smb = result.report.smb
    if smb:
        port_ok = smb.port_445.reachable if smb.port_445 else None
        if port_ok is True:
            events.append(TimelineEvent(ts, "✓", "#3fb950", "SMB scan", "Port 445 open"))
        elif port_ok is False:
            events.append(TimelineEvent(ts, "✕", "#f85149", "SMB scan", "Port 445 closed"))
        else:
            events.append(TimelineEvent(ts, "✓", "#3fb950", "SMB scan", "Config scanned"))

    svc = result.report.services
    if svc:
        stopped = [s for s in svc.services if s.status == "Stopped"]
        if stopped:
            names = ", ".join(s.name for s in stopped[:2])
            events.append(TimelineEvent(ts, "⚠", "#d29922", "Services check", f"Stopped: {names}"))
        else:
            events.append(TimelineEvent(ts, "✓", "#3fb950", "Services check", "All critical running"))

    prn = result.report.printers
    if prn:
        events.append(TimelineEvent(ts, "✓", "#3fb950", "Printer scan", f"{len(prn.printers)} printer(s)"))

    count = len(result.issues)
    if count:
        high = sum(1 for i in result.issues if i.severity >= RiskLevel.HIGH)
        detail = f"{high} HIGH, {count - high} other" if high else f"{count} issues"
        events.append(TimelineEvent(ts, "⚠", "#d29922", "Decision Engine", detail))
    else:
        events.append(TimelineEvent(ts, "✓", "#3fb950", "Decision Engine", "No issues found"))

    return list(reversed(events))


def _count_lan_devices(result: ScanResult) -> int:
    net = result.report.network
    if not net:
        return 0
    local_ips = {ip.ip_address for ip in net.ip_addresses if ip.ip_address}
    gateway_ips = {gw.next_hop for gw in net.gateways if gw.next_hop}
    count = 0
    for entry in net.arp_entries:
        ip = entry.ip_address
        if not ip or ":" in ip or ip in local_ips or ip in gateway_ips:
            continue
        parts = ip.split(".")
        try:
            first = int(parts[0])
            last = int(parts[-1])
        except (ValueError, IndexError):
            continue
        if first >= 224 or last in (0, 255):
            continue
        count += 1
    return count


def _plural(count: int, one: str, many: str) -> str:
    label = one if count == 1 else many
    return f"{count} {label}"


def _suggest_next_step(result: ScanResult) -> str:
    if not result.issues:
        return "No immediate action needed."
    worst = max(result.issues, key=lambda issue: issue.severity)
    module = (worst.related_module or "").lower()
    if module == "firewall":
        return "Check firewall rules."
    if module == "printers":
        return "Check printer status and spooler."
    if module == "services":
        return "Check required Windows services."
    if module == "smb":
        return "Check SMB sharing and credentials."
    if module == "network":
        return "Check gateway and network profile."
    if worst.recommended_actions:
        return worst.recommended_actions[0].rstrip(".") + "."
    return "Review the highest severity issue."


# Context: agent_reports/2026-07-01_fix-status-summary-report-client-summary.md
def _build_summary(result: ScanResult) -> str:
    report = result.report
    gateway_count = len(report.network.gateways) if report.network else 0
    printer_count = len(report.printers.printers) if report.printers else 0
    device_count = _count_lan_devices(result)
    issue_count = len(result.issues)
    return (
        "Found: "
        f"{_plural(gateway_count, 'gateway', 'gateways')}, "
        f"{_plural(printer_count, 'printer', 'printers')}, "
        f"{_plural(device_count, 'LAN device', 'LAN devices')}. "
        f"Issues: {issue_count}. "
        f"Suggested: {_suggest_next_step(result)}"
    )


class _ScanWorker(QThread):
    progress = Signal(str)
    finished = Signal(object)  # ScanResult

    def __init__(self, runner: PowerShellRunner) -> None:
        super().__init__()
        self._runner = runner

    def run(self) -> None:
        result = ScanSession(self._runner).run(on_progress=self.progress.emit)
        self.finished.emit(result)


# Context: agent_reports/2026-06-30_dashboard-v2.md
class DashboardPage(QWidget):
    """Dashboard with real scan data from Faza 11 onwards."""

    open_fix_center = Signal()
    open_topology = Signal()
    scan_completed = Signal(object)  # emits ScanResult after every successful scan

    def __init__(self) -> None:
        super().__init__()
        self._runner = PowerShellRunner()
        self._setup_ui()
        if get_settings().auto_scan_on_startup:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(300, self._run_scan)

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Fixed header (outside scroll) ────────────────────────────────────
        header = QFrame()
        header.setObjectName("PanelCard")
        header.setStyleSheet("QFrame#PanelCard { border-radius: 0; border-left: none;"
                             " border-right: none; border-top: none; }")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)

        self._status_label = QLabel("Not scanned yet")
        self._status_label.setStyleSheet("color: #9aa4b2;")
        h_layout.addWidget(self._status_label)
        h_layout.addSpacing(12)

        self._scan_btn = QPushButton("▶ Run Diagnostics")
        self._scan_btn.clicked.connect(self._run_scan)
        h_layout.addWidget(self._scan_btn)

        outer.addWidget(header)

        self._summary_banner = QFrame()
        self._summary_banner.setStyleSheet(
            "QFrame { background: #0a1929; border-bottom: 1px solid #1f6feb; }"
        )
        summary_layout = QHBoxLayout(self._summary_banner)
        summary_layout.setContentsMargins(16, 7, 16, 7)
        self._summary_label = QLabel("")
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet("color: #8fc7ff; font-size: 12px;")
        summary_layout.addWidget(self._summary_label)
        self._summary_banner.hide()
        outer.addWidget(self._summary_banner)

        # ── Scrollable content area ──────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(10)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Status cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        self._card_network  = StatusCard("Network",       "—", "neutral")
        self._card_smb      = StatusCard("Sharing / SMB", "—", "neutral")
        self._card_firewall = StatusCard("Firewall",      "—", "neutral")
        self._card_services = StatusCard("Services",      "—", "neutral")
        self._card_printers = StatusCard("Printers",      "—", "neutral")
        self._card_issues   = StatusCard("Issues",        "0", "ok")
        for card in (
            self._card_network, self._card_smb, self._card_firewall,
            self._card_services, self._card_printers, self._card_issues,
        ):
            cards_row.addWidget(card)
        content_layout.addLayout(cards_row)

        # Info row — sys_info:recent_scan:issues_col = 5:5:4
        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        self._sys_info_widget = SystemInfoWidget()
        info_row.addWidget(self._sys_info_widget, stretch=5)

        self._recent_scan_widget = RecentScanWidget()
        info_row.addWidget(self._recent_scan_widget, stretch=5)

        issues_col = QVBoxLayout()
        issues_col.setSpacing(8)
        self._issues_widget = IssuesRecommendationsWidget()
        self._issues_widget.open_fix_center.connect(self.open_fix_center)
        self._quick_actions_widget = QuickActionsWidget()
        self._quick_actions_widget.open_fix_center.connect(self.open_fix_center)
        issues_col.addWidget(self._issues_widget, stretch=1)
        issues_col.addWidget(self._quick_actions_widget, stretch=1)
        info_row.addLayout(issues_col, stretch=4)

        content_layout.addLayout(info_row)

        # Topology
        self._topology_widget = NetworkTopologyWidget()
        self._topology_widget.open_topology.connect(self.open_topology)
        content_layout.addWidget(self._topology_widget)

        # Timeline + Decision Assistant
        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(8)
        self._timeline_widget = ActivityTimelineWidget()
        timeline_row.addWidget(self._timeline_widget, stretch=6)
        self._decision_assistant_widget = DecisionAssistantWidget()
        timeline_row.addWidget(self._decision_assistant_widget, stretch=4)
        content_layout.addLayout(timeline_row)

        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

    # ── Scan ────────────────────────────────────────────────────────────────

    def run_scan(self) -> None:
        self._run_scan()

    def _run_scan(self) -> None:
        if hasattr(self, "_worker") and self._worker.isRunning():
            return
        self._scan_btn.setEnabled(False)
        self._status_label.setStyleSheet("color: #d29922;")
        self._worker = _ScanWorker(self._runner)
        self._worker.progress.connect(self._status_label.setText)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.start()

    def _on_scan_finished(self, result: ScanResult) -> None:
        self._update_dashboard(result)
        self._scan_btn.setEnabled(True)

    def _update_dashboard(self, result: ScanResult) -> None:
        issues = result.issues
        report = result.report

        # Status cards — with detail text matching mockup
        net_status = _module_status(issues, "network")
        net_profile = (report.network.profiles[0].category if report.network and
                       report.network.profiles else "")
        net_detail = f"{net_profile} network" if net_profile else "Network scanned"
        self._card_network.update(
            "OK" if net_status == "ok" else ("ERROR" if net_status == "critical" else "WARN"),
            net_status,
            net_detail,
        )

        smb_status = _module_status(issues, "smb")
        smb_detail = _smb_detail(report)
        self._card_smb.update(
            "OK" if smb_status == "ok" else ("ERROR" if smb_status == "critical" else "WARN"),
            smb_status,
            smb_detail,
        )

        # Firewall: not scanned separately in Dashboard run
        fw_issues = [i for i in issues if i.related_module == "firewall"]
        if fw_issues:
            fw_status = "critical" if any(i.severity >= RiskLevel.HIGH for i in fw_issues) else "warning"
            self._card_firewall.update("WARN", fw_status, f"{len(fw_issues)} issue(s) detected")
        else:
            self._card_firewall.update("—", "neutral", "Not scanned")

        svc_status = _module_status(issues, "services")
        svc_detail = _services_detail(report)
        self._card_services.update(
            "OK" if svc_status == "ok" else ("ERROR" if svc_status == "critical" else "WARN"),
            svc_status,
            svc_detail,
        )

        printer_count = len(report.printers.printers) if report.printers else 0
        printer_detail = "Printers found" if printer_count else "No printers found"
        self._card_printers.update(str(printer_count), "ok" if printer_count else "neutral", printer_detail)

        issue_count = len(issues)
        issue_status = (
            "critical" if any(i.severity >= RiskLevel.HIGH for i in issues)
            else ("warning" if issues else "ok")
        )
        issue_detail = "Review required" if issue_count else "All good"
        self._card_issues.update(str(issue_count), issue_status, issue_detail)

        # Widgets
        self._sys_info_widget.update_data(report.network)
        self._recent_scan_widget.update_data(report)
        self._issues_widget.update_data(issues)
        self._quick_actions_widget.update_data(issues)
        self._decision_assistant_widget.update_data(issues)
        self._timeline_widget.update_data(_build_timeline_events(result))
        self._topology_widget.update_data(report.network, report.printers)
        self._summary_label.setText(_build_summary(result))
        self._summary_banner.show()

        ts = result.scanned_at.replace("T", " ")
        self._status_label.setText(f"Last scan: {ts}")
        self._status_label.setStyleSheet(
            "color: #f85149;" if any(i.severity >= RiskLevel.HIGH for i in issues)
            else ("color: #d29922;" if issues else "color: #3fb950;")
        )
        self.scan_completed.emit(result)
