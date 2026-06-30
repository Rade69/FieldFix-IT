from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.core.risk_level import RiskLevel
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


class DashboardPage(QWidget):
    """Dashboard with real scan data from Faza 11 onwards."""

    open_fix_center = Signal()
    scan_completed = Signal(object)  # emits ScanResult after every successful scan

    def __init__(self) -> None:
        super().__init__()
        self._runner = PowerShellRunner()
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # ── Header ─────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("PanelCard")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)

        self._status_label = QLabel("Not scanned yet")
        self._status_label.setStyleSheet("color: #9aa4b2;")
        h_layout.addWidget(self._status_label)

        self._scan_btn = QPushButton("▶ Run Diagnostics")
        self._scan_btn.clicked.connect(self._run_scan)
        h_layout.addWidget(self._scan_btn)

        outer.addWidget(header)

        # ── Status cards ────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        self._card_network  = StatusCard("Network",   "—",  "neutral")
        self._card_smb      = StatusCard("SMB",       "—",  "neutral")
        self._card_services = StatusCard("Services",  "—",  "neutral")
        self._card_printers = StatusCard("Printers",  "—",  "neutral")
        self._card_issues   = StatusCard("Issues",    "0",  "ok")
        self._card_firewall = StatusCard("Firewall",  "—",  "neutral")
        for card in (
            self._card_network, self._card_smb, self._card_services,
            self._card_printers, self._card_issues, self._card_firewall,
        ):
            cards_row.addWidget(card)
        outer.addLayout(cards_row)

        # ── Info row ────────────────────────────────────────────────────────
        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        self._sys_info_widget = SystemInfoWidget()
        info_row.addWidget(self._sys_info_widget)

        self._recent_scan_widget = RecentScanWidget()
        info_row.addWidget(self._recent_scan_widget)

        issues_col = QVBoxLayout()
        issues_col.setSpacing(8)
        self._issues_widget = IssuesRecommendationsWidget()
        self._quick_actions_widget = QuickActionsWidget()
        self._quick_actions_widget.open_fix_center.connect(self.open_fix_center)
        issues_col.addWidget(self._issues_widget)
        issues_col.addWidget(self._quick_actions_widget)
        info_row.addLayout(issues_col)

        outer.addLayout(info_row)

        # ── Topology ────────────────────────────────────────────────────────
        self._topology_widget = NetworkTopologyWidget()
        outer.addWidget(self._topology_widget)

        # ── Timeline row ────────────────────────────────────────────────────
        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(8)
        self._timeline_widget = ActivityTimelineWidget()
        timeline_row.addWidget(self._timeline_widget, stretch=6)
        timeline_row.addWidget(DecisionAssistantWidget(), stretch=4)
        outer.addLayout(timeline_row)

        outer.addStretch(1)

    # ── Scan ────────────────────────────────────────────────────────────────

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setStyleSheet("color: #d29922;")

        def _progress(msg: str) -> None:
            self._status_label.setText(msg)
            QApplication.processEvents()

        try:
            result = ScanSession(self._runner).run(on_progress=_progress)
            self._update_dashboard(result)
        finally:
            self._scan_btn.setEnabled(True)

    def _update_dashboard(self, result: ScanResult) -> None:
        issues = result.issues
        report = result.report

        # Status cards
        self._card_network.update(
            "OK" if not any(i.related_module == "network" for i in issues) else
            ("ERROR" if _module_status(issues, "network") == "critical" else "WARN"),
            _module_status(issues, "network"),
        )
        self._card_smb.update(
            "OK" if _module_status(issues, "smb") == "ok" else
            ("ERROR" if _module_status(issues, "smb") == "critical" else "WARN"),
            _module_status(issues, "smb"),
        )
        self._card_services.update(
            "OK" if _module_status(issues, "services") == "ok" else
            ("ERROR" if _module_status(issues, "services") == "critical" else "WARN"),
            _module_status(issues, "services"),
        )
        printer_count = len(report.printers.printers) if report.printers else 0
        self._card_printers.update(str(printer_count), "ok")
        issue_count = len(issues)
        self._card_issues.update(
            str(issue_count),
            "critical" if any(i.severity >= RiskLevel.HIGH for i in issues)
            else ("warning" if issues else "ok"),
        )
        # Firewall: not scanned in Dashboard run — stays neutral
        self._card_firewall.update("—", "neutral")

        # Widgets
        self._sys_info_widget.update_data(report.network)
        self._recent_scan_widget.update_data(report)
        self._issues_widget.update_data(issues)
        self._quick_actions_widget.update_data(issues)
        self._timeline_widget.update_data(_build_timeline_events(result))
        self._topology_widget.update_data(report.network, report.printers)

        ts = result.scanned_at.replace("T", " ")
        self._status_label.setText(f"Last scan: {ts}")
        self._status_label.setStyleSheet(
            "color: #f85149;" if any(i.severity >= RiskLevel.HIGH for i in issues)
            else ("color: #d29922;" if issues else "color: #3fb950;")
        )
        self.scan_completed.emit(result)
