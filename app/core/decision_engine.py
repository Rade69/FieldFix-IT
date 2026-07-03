"""Decision Engine v1 — rule-based analysis of aggregated scan data.

Reads ScanReport (pure data), produces Issues with RiskLevel.
Never executes fix commands — recommendations are text only.
"""

from __future__ import annotations

from app.core.issue import Issue
from app.core.risk_level import RiskLevel
from app.modules.network.models import NetworkData
from app.modules.printers.models import PrintersData
from app.modules.services.models import ServicesData
from app.modules.smb.models import SmbData
from app.reports.models import ScanReport


# Context: agent_reports/2026-06-30_decision-engine.md
class DecisionEngine:
    """Stateless rule engine. Call analyze() with a ScanReport, get Issues back."""

    def analyze(self, report: ScanReport) -> tuple[Issue, ...]:
        issues: list[Issue] = []

        if report.network:
            issues.extend(self._analyze_network(report.network))

        if report.smb:
            issues.extend(self._analyze_smb(report.smb))

        if report.network and report.smb:
            issues.extend(self._analyze_combined(report.network, report.smb))

        if report.services:
            issues.extend(self._analyze_services(report.services))

        if report.printers:
            issues.extend(self._analyze_printers(report.printers))

        # Sort: HIGH first, then MEDIUM, LOW
        issues.sort(key=lambda i: i.severity, reverse=True)
        return tuple(issues)

    # ── Network ──────────────────────────────────────────────────────────────

    def _analyze_network(self, net: NetworkData) -> list[Issue]:
        issues: list[Issue] = []

        if not net.adapters:
            issues.append(Issue(
                id="NO_ACTIVE_ADAPTERS",
                title="No active network adapters found",
                severity=RiskLevel.HIGH,
                evidence=["Get-NetAdapter returned no Up adapters"],
                likely_cause="Network adapter is disabled, driver missing, or cable unplugged.",
                confidence="High",
                recommended_actions=["Check Device Manager for adapter status.", "Verify cable or Wi-Fi connection."],
                related_module="network",
            ))

        if not net.gateways:
            issues.append(Issue(
                id="NO_GATEWAY",
                title="No default gateway configured",
                severity=RiskLevel.HIGH,
                evidence=["Get-NetRoute returned no default gateway"],
                likely_cause="Network adapter has no gateway — DHCP may have failed or static IP is misconfigured.",
                confidence="High",
                recommended_actions=["Check IP configuration (ipconfig /all).", "Verify DHCP server is reachable."],
                related_module="network",
            ))
        elif net.gateway_reachable is False:
            gw_ip = net.gateways[0].next_hop if net.gateways else "unknown"
            issues.append(Issue(
                id="GATEWAY_UNREACHABLE",
                title=f"Gateway unreachable ({gw_ip})",
                severity=RiskLevel.HIGH,
                evidence=[f"Test-NetConnection to {gw_ip} failed"],
                likely_cause="Router/gateway is offline, wrong IP configured, or firewall blocks ICMP.",
                confidence="High",
                recommended_actions=["Ping gateway manually.", "Check physical connection to router.", "Verify IP and subnet mask."],
                related_module="network",
            ))

        for profile in net.profiles:
            if profile.category == "Public":
                issues.append(Issue(
                    id="PUBLIC_NETWORK_PROFILE",
                    title=f"Network profile is Public ({profile.interface_alias})",
                    severity=RiskLevel.MEDIUM,
                    evidence=[f"Get-NetConnectionProfile: {profile.name} = Public"],
                    likely_cause="Public profile blocks file sharing, Network Discovery, and printer sharing by default.",
                    confidence="High",
                    recommended_actions=["Change to Private: Set-NetConnectionProfile -InterfaceAlias '...' -NetworkCategory Private"],
                    related_module="network",
                    fix_id="SET_NETWORK_PRIVATE",
                ))

        return issues

    # ── SMB ──────────────────────────────────────────────────────────────────

    def _analyze_smb(self, smb: SmbData) -> list[Issue]:
        issues: list[Issue] = []

        sc = smb.server_config
        if sc and sc.smb1_enabled is True:
            issues.append(Issue(
                id="SMB1_ENABLED_SERVER",
                title="SMB1 enabled on this server — security risk",
                severity=RiskLevel.HIGH,
                evidence=["Get-SmbServerConfiguration: EnableSMB1Protocol = True"],
                likely_cause="SMB1 is a legacy protocol vulnerable to EternalBlue/WannaCry. Should be disabled.",
                confidence="High",
                recommended_actions=["Set-SmbServerConfiguration -EnableSMB1Protocol $false"],
                related_module="smb",
            ))

        cc = smb.client_config
        if cc and cc.smb1_enabled is True:
            issues.append(Issue(
                id="SMB1_ENABLED_CLIENT",
                title="SMB1 enabled on this client",
                severity=RiskLevel.MEDIUM,
                evidence=["Get-SmbClientConfiguration: EnableSMB1Protocol = True"],
                likely_cause="Client-side SMB1 allows connections to vulnerable legacy servers.",
                confidence="High",
                recommended_actions=["Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol"],
                related_module="smb",
            ))

        if cc and cc.enable_insecure_guest_logons is True:
            issues.append(Issue(
                id="GUEST_LOGONS_ENABLED",
                title="Insecure guest logons enabled",
                severity=RiskLevel.MEDIUM,
                evidence=["Get-SmbClientConfiguration: EnableInsecureGuestLogons = True"],
                likely_cause="Allows unauthenticated access to network shares — security risk in mixed environments.",
                confidence="High",
                recommended_actions=["Set-SmbClientConfiguration -EnableInsecureGuestLogons $false"],
                related_module="smb",
            ))

        if smb.port_445 and smb.port_445.reachable is False:
            target = smb.port_445.target_ip
            issues.append(Issue(
                id="PORT_445_CLOSED",
                title=f"Port 445 not reachable on {target}",
                severity=RiskLevel.HIGH,
                evidence=[f"Test-NetConnection {target}:445 = False"],
                likely_cause="Firewall blocking port 445, or Server service stopped on target machine.",
                confidence="High",
                recommended_actions=[
                    "Enable 'File and Printer Sharing' firewall rules on target.",
                    "Verify Server (LanmanServer) service is running on target.",
                ],
                related_module="smb",
                fix_id="ENABLE_FILE_PRINTER_SHARING",
            ))

        _net_view_rules = {
            53:   ("NET_VIEW_ERROR_53",   RiskLevel.HIGH,   "Network path not found (error 53)",
                   "Routing or DNS problem — target IP not reachable.",
                   ["Verify IP address is correct.", "Check routing and firewall."]),
            6118: ("NET_VIEW_ERROR_6118", RiskLevel.MEDIUM, "Net View error 6118 — server list unavailable",
                   "Network Discovery or Computer Browser service is stopped or blocked.",
                   ["Enable Network Discovery.", "Start FDResPub and fdPHost services."]),
            1272: ("NET_VIEW_ERROR_1272", RiskLevel.MEDIUM, "Guest access blocked (error 1272)",
                   "EnableInsecureGuestLogons is disabled on this client.",
                   ["Enable guest logons or provide credentials: net use \\\\IP /user:username"]),
            5:    ("NET_VIEW_ERROR_5",    RiskLevel.MEDIUM, "Access denied (error 5)",
                   "Share permissions deny access for this user account.",
                   ["Check share and NTFS permissions on target.", "Verify user account has access."]),
            86:   ("NET_VIEW_ERROR_86",   RiskLevel.MEDIUM, "Wrong network password (error 86)",
                   "Authentication failed — incorrect password for the user account.",
                   ["Re-enter credentials: net use \\\\IP /user:username password"]),
            1326: ("NET_VIEW_ERROR_1326", RiskLevel.MEDIUM, "Logon failure — unknown user or bad password (error 1326)",
                   "User account not found or password incorrect on target machine.",
                   ["Verify username and password.", "Check user exists on target."]),
        }

        code = smb.net_view_error_code
        if code and code in _net_view_rules:
            issue_id, severity, title, cause, actions = _net_view_rules[code]
            issues.append(Issue(
                id=issue_id,
                title=title,
                severity=severity,
                evidence=[f"net view returned error {code}"],
                likely_cause=cause,
                confidence="High",
                recommended_actions=actions,
                related_module="smb",
            ))

        return issues

    # ── Combined Network + SMB ────────────────────────────────────────────────

    def _analyze_combined(self, net: NetworkData, smb: SmbData) -> list[Issue]:
        issues: list[Issue] = []

        gateway_ok = net.gateway_reachable is True
        port_445 = smb.port_445

        # ping ok + port 445 fail = firewall/SMB port problem on target
        if gateway_ok and port_445 and port_445.reachable is False:
            issues.append(Issue(
                id="FIREWALL_PORT_445_BLOCKED",
                title=f"Firewall or service blocking SMB on {port_445.target_ip}",
                severity=RiskLevel.HIGH,
                evidence=[
                    f"Gateway {net.gateways[0].next_hop if net.gateways else '?'} is reachable",
                    f"Port 445 on {port_445.target_ip} is NOT reachable",
                ],
                likely_cause="Local network path is OK but SMB port is blocked — firewall rule on target or Server service stopped.",
                confidence="High",
                recommended_actions=[
                    "On target: enable 'File and Printer Sharing' firewall rules.",
                    "On target: verify Server (LanmanServer) service is Running.",
                ],
                related_module="smb",
                fix_id="ENABLE_FILE_PRINTER_SHARING",
            ))

        # net view 6118 + port 445 ok = browsing problem, not SMB connectivity problem
        if smb.net_view_error_code == 6118 and port_445 and port_445.reachable is True:
            issues.append(Issue(
                id="BROWSING_PROBLEM_NOT_SMB",
                title="Network browsing issue — SMB port is open",
                severity=RiskLevel.MEDIUM,
                evidence=[
                    f"Port 445 on {port_445.target_ip} is reachable",
                    "net view returned error 6118 (server list unavailable)",
                ],
                likely_cause="SMB connectivity works (port 445 open) but network browsing fails. "
                             "FDResPub, fdPHost, or Computer Browser service is likely stopped.",
                confidence="High",
                recommended_actions=[
                    "Start FDResPub and fdPHost services on target.",
                    "Enable 'Network Discovery' firewall rules on target.",
                ],
                related_module="smb",
                fix_id="ENABLE_NETWORK_DISCOVERY",
            ))

        return issues

    # ── Services ─────────────────────────────────────────────────────────────

    def _analyze_services(self, svc: ServicesData) -> list[Issue]:
        issues: list[Issue] = []

        _service_rules: dict[str, tuple[RiskLevel, str, list[str], str | None]] = {
            "LanmanServer": (
                RiskLevel.HIGH,
                "Server service stopped — file and printer sharing unavailable",
                ["Start-Service LanmanServer", "Set-Service LanmanServer -StartupType Automatic"],
                None,
            ),
            "LanmanWorkstation": (
                RiskLevel.HIGH,
                "Workstation service stopped — cannot connect to network shares",
                ["Start-Service LanmanWorkstation", "Set-Service LanmanWorkstation -StartupType Automatic"],
                None,
            ),
            "Spooler": (
                RiskLevel.MEDIUM,
                "Print Spooler stopped — printing not available",
                ["Start-Service Spooler", "Set-Service Spooler -StartupType Automatic"],
                "START_PRINT_SPOOLER",
            ),
            "FDResPub": (
                RiskLevel.LOW,
                "FDResPub stopped — this PC not visible in Network Discovery",
                ["Start-Service FDResPub"],
                "START_FDRESPUB",
            ),
            "fdPHost": (
                RiskLevel.LOW,
                "fdPHost stopped — may affect network device discovery",
                ["Start-Service fdPHost"],
                None,
            ),
        }

        for s in svc.services:
            if s.name in _service_rules and s.status == "Stopped":
                severity, title, actions, fix_id = _service_rules[s.name]
                issues.append(Issue(
                    id=f"SERVICE_STOPPED_{s.name.upper()}",
                    title=title,
                    severity=severity,
                    evidence=[f"Get-Service {s.name}: Status = Stopped"],
                    likely_cause=f"Service '{s.name}' ({s.display_name}) is not running.",
                    confidence="High",
                    recommended_actions=actions,
                    related_module="services",
                    fix_id=fix_id,
                ))

        return issues

    # ── Printers ─────────────────────────────────────────────────────────────

    def _analyze_printers(self, prn: PrintersData) -> list[Issue]:
        issues: list[Issue] = []

        _status_ok = {"Normal", "Printing"}

        for p in prn.printers:
            if p.status and p.status not in _status_ok and p.status != "NotFound":
                severity = RiskLevel.HIGH if p.status in {"Error", "Offline"} else RiskLevel.MEDIUM
                issues.append(Issue(
                    id=f"PRINTER_{p.status.upper()}_{p.name.replace(' ', '_').upper()[:20]}",
                    title=f"Printer '{p.name}' — {p.status}",
                    severity=severity,
                    evidence=[f"Get-Printer: {p.name} Status = {p.status}"],
                    likely_cause=_printer_cause(p.status),
                    confidence="Medium",
                    recommended_actions=_printer_actions(p.status, p.name),
                    related_module="printers",
                ))

        for j in prn.print_jobs:
            if "Error" in j.status:
                issues.append(Issue(
                    id=f"PRINT_JOB_ERROR_{j.job_id}",
                    title=f"Stuck print job: '{j.document_name}' on {j.printer_name}",
                    severity=RiskLevel.LOW,
                    evidence=[f"Get-PrintJob Id={j.job_id}: Status = {j.status}"],
                    likely_cause="Print job is stuck in error state — may block the print queue.",
                    confidence="High",
                    recommended_actions=[
                        f"Remove-PrintJob -PrinterName '{j.printer_name}' -ID {j.job_id}",
                        "Restart Print Spooler if queue remains stuck.",
                    ],
                    related_module="printers",
                ))

        return issues


def _printer_cause(status: str) -> str:
    return {
        "Offline":  "Printer is offline — powered off or not connected to network.",
        "Error":    "Printer reported an error — check paper, toner, or hardware.",
        "Paused":   "Printer is paused — print queue is not processing jobs.",
        "PaperJam": "Paper jam detected — requires physical intervention.",
        "PaperOut": "Paper tray is empty.",
    }.get(status, f"Printer reported status '{status}' — check printer control panel.")


def _printer_actions(status: str, name: str) -> list[str]:
    base = [f"Check physical state of '{name}'."]
    if status == "Offline":
        return base + ["Power on printer and verify network/USB connection."]
    if status in {"Error", "PaperJam"}:
        return base + ["Clear any paper jams or error conditions on printer panel."]
    if status == "Paused":
        return base + [f"Resume printer: Resume-PrintJob -PrinterName '{name}'"]
    if status == "PaperOut":
        return base + ["Load paper into printer tray."]
    return base + ["Restart printer and check connection."]
