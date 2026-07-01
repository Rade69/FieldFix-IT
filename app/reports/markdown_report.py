from __future__ import annotations

from app.core.issue import Issue, RiskLevel
from app.modules.network.models import NetworkData
from app.modules.printers.models import PrintersData
from app.modules.services.models import ServicesData
from app.modules.smb.models import SmbData
from app.reports.models import ScanReport

_NOT_SCANNED = "_Not scanned — section was not included in this report._"
_YES = "✓ Yes"
_NO = "✕ No"
_UNKNOWN = "—"


def _bool_str(value: bool | None, true_good: bool = True) -> str:
    if value is None:
        return _UNKNOWN
    if value:
        return _YES if true_good else _NO
    return _NO if true_good else _YES


# Context: agent_reports/2026-06-30_report-generator.md
def write_markdown(report: ScanReport, issues: tuple[Issue, ...] = ()) -> str:
    lines: list[str] = []

    lines += [
        "# FieldFix IT — Diagnostic Report",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Generated | {report.generated_at} |",
        f"| Hostname  | {report.hostname or _UNKNOWN} |",
        "",
        "---",
        "",
    ]

    lines += _client_summary_section(report, issues)
    lines += ["## Technical Details", ""]

    if issues:
        lines += _issues_section(issues)

    lines += _network_section(report.network)
    lines += _smb_section(report.smb, report.smb_target_ip)
    lines += _services_section(report.services)
    lines += _printers_section(report.printers)

    lines += [
        "---",
        "",
        f"*FieldFix IT — Windows IT Diagnostics Tool*",
        "",
    ]

    return "\n".join(lines)


def _suggested_next_steps(issues: tuple[Issue, ...]) -> list[str]:
    if not issues:
        return ["No immediate action needed."]
    steps: list[str] = []
    for issue in issues[:3]:
        if issue.recommended_actions:
            steps.append(issue.recommended_actions[0])
        elif issue.likely_cause:
            steps.append(f"Review: {issue.likely_cause}")
        else:
            steps.append(f"Review: {issue.title}")
    return steps


# Context: agent_reports/2026-07-01_fix-status-summary-report-client-summary.md
def _client_summary_section(report: ScanReport, issues: tuple[Issue, ...]) -> list[str]:
    lines = ["## Client Summary", ""]
    lines += [
        f"- **Issues found:** {len(issues)}",
        "- **Suggested next steps:**",
    ]
    for step in _suggested_next_steps(issues):
        lines.append(f"  - {step}")
    lines.append("")

    printers = report.printers.printers if report.printers else ()
    if printers:
        lines += ["### Printers", "", "| Name | Status |", "|------|--------|"]
        for printer in printers:
            lines.append(f"| {printer.name} | {printer.status or _UNKNOWN} |")
        lines.append("")
    else:
        lines += ["### Printers", "", "_No printers found or printer scan was not included._", ""]

    return lines + ["---", ""]


# ── Issues ────────────────────────────────────────────────────────────────────

_RISK_ICON = {RiskLevel.HIGH: "🔴", RiskLevel.MEDIUM: "🟡", RiskLevel.LOW: "🟢", RiskLevel.CRITICAL: "🔴"}


def _issues_section(issues: tuple[Issue, ...]) -> list[str]:
    high = [i for i in issues if i.severity >= RiskLevel.HIGH]
    med  = [i for i in issues if i.severity == RiskLevel.MEDIUM]
    low  = [i for i in issues if i.severity < RiskLevel.MEDIUM]

    lines = [f"## ⚠ Diagnostic Issues ({len(issues)} found)", ""]
    lines += [
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| 🔴 HIGH   | {len(high)} |",
        f"| 🟡 MEDIUM | {len(med)} |",
        f"| 🟢 LOW    | {len(low)} |",
        "",
    ]

    for issue in issues:
        icon = _RISK_ICON.get(issue.severity, "●")
        lines += [f"### {icon} {issue.title}", ""]
        lines += [f"**Severity:** {issue.severity}  |  **Confidence:** {issue.confidence}  |  **Module:** {issue.related_module or '—'}", ""]
        if issue.likely_cause:
            lines += [f"**Likely cause:** {issue.likely_cause}", ""]
        if issue.evidence:
            lines += ["**Evidence:**"]
            for e in issue.evidence:
                lines.append(f"- `{e}`")
            lines.append("")
        if issue.recommended_actions:
            lines += ["**Recommended actions:**"]
            for a in issue.recommended_actions:
                lines.append(f"1. {a}")
            lines.append("")

    return lines + ["---", ""]


# ── Network ────────────────────────────────────────────────────────────────────

def _network_section(data: NetworkData | None) -> list[str]:
    lines = ["## 🌐 Network", ""]
    if data is None:
        return lines + [_NOT_SCANNED, "", "---", ""]

    lines += [f"**Scan duration:** {data.scan_duration_ms / 1000:.2f}s", ""]

    # Adapters
    if data.adapters:
        lines += [f"### Active Adapters ({len(data.adapters)})", ""]
        lines += ["| Name | Description | Speed | MAC |",
                  "|------|-------------|-------|-----|"]
        for a in data.adapters:
            from app.modules.network.scanner import _format_speed
            speed = _format_speed(a.link_speed_bps) or _UNKNOWN
            lines.append(f"| {a.name} | {a.description} | {speed} | {a.mac_address or _UNKNOWN} |")
        lines.append("")

    # IP addressing
    if data.ip_addresses:
        lines += ["### IP Addressing", "",
                  "| Interface | IP Address | Prefix |",
                  "|-----------|------------|--------|"]
        for ip in data.ip_addresses:
            lines.append(f"| {ip.interface_alias} | {ip.ip_address} | /{ip.prefix_length or '?'} |")
        lines.append("")

    # Gateways
    if data.gateways:
        reach = _UNKNOWN
        if data.gateway_reachable is not None:
            reach = "✓ Reachable" if data.gateway_reachable else "✕ Unreachable"
        lines += ["### Gateway", "",
                  "| Interface | Next Hop | Metric | Reachable |",
                  "|-----------|----------|--------|-----------|"]
        for i, gw in enumerate(data.gateways):
            lines.append(
                f"| {gw.interface_alias} | {gw.next_hop} | {gw.metric or _UNKNOWN} "
                f"| {reach if i == 0 else _UNKNOWN} |"
            )
        lines.append("")

    # DNS
    if data.dns:
        lines += ["### DNS", "",
                  "| Interface | Servers |",
                  "|-----------|---------|"]
        for d in data.dns:
            lines.append(f"| {d.interface_alias} | {', '.join(d.servers)} |")
        lines.append("")

    # Network profiles
    if data.profiles:
        lines += ["### Network Profiles", "",
                  "| Name | Interface | Category |",
                  "|------|-----------|----------|"]
        for p in data.profiles:
            lines.append(f"| {p.name} | {p.interface_alias} | {p.category} |")
        lines.append("")

    if data.errors:
        lines += ["### ⚠ Scan Warnings", ""]
        for e in data.errors:
            lines.append(f"- {e}")
        lines.append("")

    return lines + ["---", ""]


# ── SMB ───────────────────────────────────────────────────────────────────────

def _smb_section(data: SmbData | None, target_ip: str) -> list[str]:
    lines = ["## 📁 SMB / File Sharing", ""]
    if data is None:
        return lines + [_NOT_SCANNED, "", "---", ""]

    if target_ip:
        lines += [f"**Target IP:** {target_ip}", ""]

    # Server config
    sc = data.server_config
    if sc:
        lines += ["### Server Configuration", "",
                  "| Setting | Value |",
                  "|---------|-------|",
                  f"| SMB1 Enabled | {'✕ Disabled (good)' if sc.smb1_enabled is False else ('⚠ Enabled (risk)' if sc.smb1_enabled else _UNKNOWN)} |",
                  f"| SMB2 Enabled | {_bool_str(sc.smb2_enabled)} |",
                  f"| Security Signature Required | {_bool_str(sc.require_security_signature)} |",
                  f"| Security Signature Enabled  | {_bool_str(sc.enable_security_signature)} |",
                  ""]

    # Client config
    cc = data.client_config
    if cc:
        lines += ["### Client Configuration", "",
                  "| Setting | Value |",
                  "|---------|-------|",
                  f"| SMB1 Enabled | {_bool_str(cc.smb1_enabled, true_good=False)} |",
                  f"| Insecure Guest Logons | {_bool_str(cc.enable_insecure_guest_logons, true_good=False)} |",
                  f"| Security Signature Required | {_bool_str(cc.require_security_signature)} |",
                  ""]

    # Local shares
    if data.shares:
        lines += [f"### Local Shares ({len(data.shares)})", "",
                  "| Name | Path | Description | Type |",
                  "|------|------|-------------|------|"]
        for s in data.shares:
            lines.append(f"| {s.name} | {s.path or _UNKNOWN} | {s.description or _UNKNOWN} | {s.share_type} |")
        lines.append("")

    # Port 445
    if data.port_445:
        p = data.port_445
        reach = "✓ Open" if p.reachable else ("✕ Closed/Filtered" if p.reachable is False else _UNKNOWN)
        lines += [f"### Port 445 — {p.target_ip}", "",
                  f"- **Reachable:** {reach}", ""]

    # Net View
    if data.net_view_success is not None:
        lines += ["### Net View", ""]
        if data.net_view_success:
            lines += [f"**Result:** ✓ Success ({len(data.net_view_entries)} share(s) visible)", ""]
            if data.net_view_entries:
                lines += ["| Share | Type | Comment |",
                          "|-------|------|---------|"]
                for e in data.net_view_entries:
                    lines.append(f"| {e.name} | {e.share_type} | {e.comment or _UNKNOWN} |")
                lines.append("")
        else:
            code = data.net_view_error_code
            lines += [f"**Result:** ✕ Failed{f' (error {code})' if code else ''}", ""]

    if data.errors:
        lines += ["### ⚠ Scan Warnings", ""]
        for e in data.errors:
            lines.append(f"- {e}")
        lines.append("")

    return lines + ["---", ""]


# ── Services ──────────────────────────────────────────────────────────────────

def _services_section(data: ServicesData | None) -> list[str]:
    lines = ["## ⚙ Services", ""]
    if data is None:
        return lines + [_NOT_SCANNED, "", "---", ""]

    if data.services:
        lines += ["| Service | Display Name | Status | Startup | Purpose |",
                  "|---------|-------------|--------|---------|---------|"]
        for s in data.services:
            icon = "✓" if s.status == "Running" else ("✕" if s.status == "Stopped" else "●")
            lines.append(
                f"| {s.name} | {s.display_name or _UNKNOWN} "
                f"| {icon} {s.status} | {s.start_type or _UNKNOWN} | {s.required_for} |"
            )
        lines.append("")

    if data.errors:
        lines += ["### ⚠ Scan Warnings", ""]
        for e in data.errors:
            lines.append(f"- {e}")
        lines.append("")

    return lines + ["---", ""]


# ── Printers ──────────────────────────────────────────────────────────────────

def _printers_section(data: PrintersData | None) -> list[str]:
    lines = ["## 🖨 Printers", ""]
    if data is None:
        return lines + [_NOT_SCANNED, "", "---", ""]

    if data.printers:
        lines += [f"### Installed Printers ({len(data.printers)})", "",
                  "| Name | Type | Status | Startup Type | Default | Jobs |",
                  "|------|------|--------|-------------|---------|------|"]
        for p in data.printers:
            icon = "✓" if p.status == "Normal" else "✕"
            default = "★" if p.is_default else ""
            lines.append(
                f"| {p.name} | {p.printer_type or _UNKNOWN} "
                f"| {icon} {p.status} | {p.driver_name or _UNKNOWN} "
                f"| {default} | {p.job_count} |"
            )
        lines.append("")

    if data.print_jobs:
        lines += [f"### Active Print Jobs ({len(data.print_jobs)})", "",
                  "| ID | Printer | Document | User | Pages | Status |",
                  "|----|---------|----------|------|-------|--------|"]
        for j in data.print_jobs:
            lines.append(
                f"| {j.job_id} | {j.printer_name} | {j.document_name} "
                f"| {j.user_name} | {j.total_pages or _UNKNOWN} | {j.status} |"
            )
        lines.append("")

    if data.errors:
        lines += ["### ⚠ Scan Warnings", ""]
        for e in data.errors:
            lines.append(f"- {e}")
        lines.append("")

    return lines + ["---", ""]
