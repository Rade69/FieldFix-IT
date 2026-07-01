from __future__ import annotations

import html

from app.core.issue import Issue, RiskLevel
from app.modules.network.models import NetworkData
from app.modules.printers.models import PrintersData
from app.modules.services.models import ServicesData
from app.modules.smb.models import SmbData
from app.reports.models import ScanReport

_NOT_SCANNED = "<p><em>Not scanned — section was not included in this report.</em></p>"

_CSS = """
body{font-family:Arial,sans-serif;max-width:1000px;margin:40px auto;color:#333;line-height:1.5}
h1{color:#1a3a5c;border-bottom:3px solid #1a3a5c;padding-bottom:8px}
h2{color:#1a3a5c;margin-top:32px;border-bottom:1px solid #ccc;padding-bottom:4px}
h3{color:#2c5282;margin-top:20px}
table{border-collapse:collapse;width:100%;margin-bottom:16px;font-size:14px}
th{background:#1a3a5c;color:#fff;padding:8px 12px;text-align:left}
td{padding:7px 12px;border-bottom:1px solid #e0e0e0}
tr:nth-child(even) td{background:#f7f9fc}
.ok{color:#2e7d32;font-weight:bold}
.err{color:#c62828;font-weight:bold}
.warn{color:#e65100;font-weight:bold}
.muted{color:#757575}
.meta-table td{width:50%}
footer{text-align:center;margin-top:48px;color:#999;font-size:12px;border-top:1px solid #eee;padding-top:16px}
hr{border:1px solid #e0e0e0;margin:28px 0}
"""


def _e(text: object) -> str:
    """HTML-escape a value and return as string."""
    return html.escape(str(text) if text is not None else "")


def _bool_cell(value: bool | None, true_good: bool = True) -> str:
    if value is None:
        return '<span class="muted">—</span>'
    if value:
        cls = "ok" if true_good else "err"
        label = "✓ Yes" if true_good else "✕ Yes"
    else:
        cls = "err" if true_good else "ok"
        label = "✕ No" if true_good else "✓ No"
    return f'<span class="{cls}">{label}</span>'


def write_html(report: ScanReport, issues: tuple[Issue, ...] = ()) -> str:
    body_parts: list[str] = []

    body_parts.append(
        f"""<h1>FieldFix IT — Diagnostic Report</h1>
<table class="meta-table"><tbody>
<tr><td><strong>Generated</strong></td><td>{_e(report.generated_at)}</td></tr>
<tr><td><strong>Hostname</strong></td><td>{_e(report.hostname) or '<span class="muted">—</span>'}</td></tr>
</tbody></table>"""
    )

    body_parts.append(_client_summary_html(report, issues))
    body_parts.append("<h2>Technical Details</h2>")

    if issues:
        body_parts.append(_issues_html(issues))

    body_parts.append(_network_html(report.network))
    body_parts.append(_smb_html(report.smb, report.smb_target_ip))
    body_parts.append(_services_html(report.services))
    body_parts.append(_printers_html(report.printers))

    body = "\n".join(body_parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FieldFix IT — Diagnostic Report</title>
<style>{_CSS}</style>
</head>
<body>
{body}
<footer>FieldFix IT — Windows IT Diagnostics Tool &nbsp;|&nbsp; {_e(report.generated_at)}</footer>
</body>
</html>"""


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


def _client_summary_html(report: ScanReport, issues: tuple[Issue, ...]) -> str:
    s = "<h2>Client Summary</h2>\n"
    s += f"<p><strong>Issues found:</strong> {_e(len(issues))}</p>\n"
    s += "<p><strong>Suggested next steps:</strong></p>\n<ol>\n"
    for step in _suggested_next_steps(issues):
        s += f"<li>{_e(step)}</li>\n"
    s += "</ol>\n"

    printers = report.printers.printers if report.printers else ()
    if printers:
        s += "<h3>Printers</h3>\n"
        s += "<table><thead><tr><th>Name</th><th>Status</th></tr></thead><tbody>\n"
        for printer in printers:
            s += f"<tr><td>{_e(printer.name)}</td><td>{_e(printer.status or '—')}</td></tr>\n"
        s += "</tbody></table>\n"
    else:
        s += "<h3>Printers</h3>\n<p><em>No printers found or printer scan was not included.</em></p>\n"

    return s + "<hr>\n"


# ── Issues ───────────────────────────────────────────────────────────────────

_RISK_COLOR = {
    RiskLevel.CRITICAL: "#c62828",
    RiskLevel.HIGH:     "#c62828",
    RiskLevel.MEDIUM:   "#e65100",
    RiskLevel.LOW:      "#2e7d32",
}
_RISK_ICON = {
    RiskLevel.CRITICAL: "🔴",
    RiskLevel.HIGH:     "🔴",
    RiskLevel.MEDIUM:   "🟡",
    RiskLevel.LOW:      "🟢",
}


def _issues_html(issues: tuple[Issue, ...]) -> str:
    high   = sum(1 for i in issues if i.severity >= RiskLevel.HIGH)
    medium = sum(1 for i in issues if i.severity == RiskLevel.MEDIUM)
    low    = sum(1 for i in issues if i.severity < RiskLevel.MEDIUM)

    s = (f"<h2>⚠ Diagnostic Issues ({len(issues)} found)</h2>\n"
         "<table class='meta-table'><tbody>"
         f"<tr><td>🔴 HIGH</td><td><strong style='color:#c62828'>{high}</strong></td></tr>"
         f"<tr><td>🟡 MEDIUM</td><td><strong style='color:#e65100'>{medium}</strong></td></tr>"
         f"<tr><td>🟢 LOW</td><td><strong style='color:#2e7d32'>{low}</strong></td></tr>"
         "</tbody></table>\n")

    for issue in issues:
        color = _RISK_COLOR.get(issue.severity, "#333")
        icon  = _RISK_ICON.get(issue.severity, "●")
        s += (f"<h3 style='color:{color}'>{icon} {_e(issue.title)}</h3>\n"
              f"<p class='muted'>"
              f"Severity: <strong style='color:{color}'>{_e(str(issue.severity))}</strong> &nbsp;|&nbsp; "
              f"Confidence: {_e(issue.confidence)} &nbsp;|&nbsp; "
              f"Module: {_e(issue.related_module or '—')}</p>\n")

        if issue.likely_cause:
            s += f"<p><strong>Likely cause:</strong> {_e(issue.likely_cause)}</p>\n"

        if issue.evidence:
            s += "<p><strong>Evidence:</strong></p><ul>\n"
            for ev in issue.evidence:
                s += f"<li><code>{_e(ev)}</code></li>\n"
            s += "</ul>\n"

        if issue.recommended_actions:
            s += "<p><strong>Recommended actions:</strong></p><ol>\n"
            for act in issue.recommended_actions:
                s += f"<li>{_e(act)}</li>\n"
            s += "</ol>\n"

    return s + "<hr>\n"


# ── Network ────────────────────────────────────────────────────────────────────

def _network_html(data: NetworkData | None) -> str:
    s = "<h2>🌐 Network</h2>\n"
    if data is None:
        return s + _NOT_SCANNED

    s += f"<p class='muted'>Scan duration: {data.scan_duration_ms / 1000:.2f}s</p>\n"

    if data.adapters:
        from app.modules.network.scanner import _format_speed
        s += f"<h3>Active Adapters ({len(data.adapters)})</h3>\n"
        s += "<table><thead><tr><th>Name</th><th>Description</th><th>Speed</th><th>MAC</th></tr></thead><tbody>\n"
        for a in data.adapters:
            s += (f"<tr><td>{_e(a.name)}</td><td>{_e(a.description)}</td>"
                  f"<td>{_e(_format_speed(a.link_speed_bps) or '—')}</td>"
                  f"<td class='muted'>{_e(a.mac_address or '—')}</td></tr>\n")
        s += "</tbody></table>\n"

    if data.ip_addresses:
        s += "<h3>IP Addressing</h3>\n"
        s += "<table><thead><tr><th>Interface</th><th>IP Address</th><th>Prefix</th></tr></thead><tbody>\n"
        for ip in data.ip_addresses:
            s += (f"<tr><td>{_e(ip.interface_alias)}</td><td>{_e(ip.ip_address)}</td>"
                  f"<td>/{_e(ip.prefix_length or '?')}</td></tr>\n")
        s += "</tbody></table>\n"

    if data.gateways:
        reach_html = ""
        if data.gateway_reachable is not None:
            ok = data.gateway_reachable
            reach_html = (f'<span class="ok">✓ Reachable</span>' if ok
                          else '<span class="err">✕ Unreachable</span>')
        s += "<h3>Gateway</h3>\n"
        s += "<table><thead><tr><th>Interface</th><th>Next Hop</th><th>Metric</th><th>Reachable</th></tr></thead><tbody>\n"
        for i, gw in enumerate(data.gateways):
            s += (f"<tr><td>{_e(gw.interface_alias)}</td><td>{_e(gw.next_hop)}</td>"
                  f"<td class='muted'>{_e(gw.metric or '—')}</td>"
                  f"<td>{reach_html if i == 0 else ''}</td></tr>\n")
        s += "</tbody></table>\n"

    if data.dns:
        s += "<h3>DNS</h3>\n"
        s += "<table><thead><tr><th>Interface</th><th>Servers</th></tr></thead><tbody>\n"
        for d in data.dns:
            s += f"<tr><td>{_e(d.interface_alias)}</td><td>{_e(', '.join(d.servers))}</td></tr>\n"
        s += "</tbody></table>\n"

    if data.errors:
        s += "<h3>⚠ Scan Warnings</h3>\n<ul>\n"
        for e in data.errors:
            s += f"<li class='warn'>{_e(e)}</li>\n"
        s += "</ul>\n"

    return s + "<hr>\n"


# ── SMB ───────────────────────────────────────────────────────────────────────

def _smb_html(data: SmbData | None, target_ip: str) -> str:
    s = "<h2>📁 SMB / File Sharing</h2>\n"
    if data is None:
        return s + _NOT_SCANNED

    if target_ip:
        s += f"<p><strong>Target IP:</strong> {_e(target_ip)}</p>\n"

    sc = data.server_config
    if sc:
        smb1_cell = ('<span class="ok">✕ Disabled (good)</span>' if sc.smb1_enabled is False
                     else ('<span class="err">⚠ Enabled (risk)</span>' if sc.smb1_enabled
                           else '<span class="muted">—</span>'))
        s += ("<h3>Server Configuration</h3>\n"
              "<table><thead><tr><th>Setting</th><th>Value</th></tr></thead><tbody>\n"
              f"<tr><td>SMB1 Enabled</td><td>{smb1_cell}</td></tr>\n"
              f"<tr><td>SMB2 Enabled</td><td>{_bool_cell(sc.smb2_enabled)}</td></tr>\n"
              f"<tr><td>Security Signature Required</td><td>{_bool_cell(sc.require_security_signature)}</td></tr>\n"
              f"<tr><td>Security Signature Enabled</td><td>{_bool_cell(sc.enable_security_signature)}</td></tr>\n"
              "</tbody></table>\n")

    cc = data.client_config
    if cc:
        s += ("<h3>Client Configuration</h3>\n"
              "<table><thead><tr><th>Setting</th><th>Value</th></tr></thead><tbody>\n"
              f"<tr><td>SMB1 Enabled</td><td>{_bool_cell(cc.smb1_enabled, true_good=False)}</td></tr>\n"
              f"<tr><td>Insecure Guest Logons</td><td>{_bool_cell(cc.enable_insecure_guest_logons, true_good=False)}</td></tr>\n"
              f"<tr><td>Security Signature Required</td><td>{_bool_cell(cc.require_security_signature)}</td></tr>\n"
              "</tbody></table>\n")

    if data.shares:
        s += f"<h3>Local Shares ({len(data.shares)})</h3>\n"
        s += "<table><thead><tr><th>Name</th><th>Path</th><th>Description</th><th>Type</th></tr></thead><tbody>\n"
        for sh in data.shares:
            s += (f"<tr><td><strong>{_e(sh.name)}</strong></td><td class='muted'>{_e(sh.path or '—')}</td>"
                  f"<td>{_e(sh.description or '—')}</td><td class='muted'>{_e(sh.share_type)}</td></tr>\n")
        s += "</tbody></table>\n"

    if data.port_445:
        p = data.port_445
        ok = p.reachable
        reach_html = ('<span class="ok">✓ Open</span>' if ok
                      else ('<span class="err">✕ Closed/Filtered</span>' if ok is False
                            else '<span class="muted">—</span>'))
        s += f"<h3>Port 445 — {_e(p.target_ip)}</h3>\n<p>Reachable: {reach_html}</p>\n"

    if data.net_view_success is not None:
        s += "<h3>Net View</h3>\n"
        if data.net_view_success:
            s += f"<p><span class='ok'>✓ Success</span> — {len(data.net_view_entries)} share(s) visible</p>\n"
            if data.net_view_entries:
                s += "<table><thead><tr><th>Share</th><th>Type</th><th>Comment</th></tr></thead><tbody>\n"
                for e in data.net_view_entries:
                    s += f"<tr><td>{_e(e.name)}</td><td class='muted'>{_e(e.share_type)}</td><td>{_e(e.comment or '—')}</td></tr>\n"
                s += "</tbody></table>\n"
        else:
            code = data.net_view_error_code
            s += f"<p><span class='err'>✕ Failed</span>{f' (error {code})' if code else ''}</p>\n"

    if data.errors:
        s += "<h3>⚠ Scan Warnings</h3>\n<ul>\n"
        for e in data.errors:
            s += f"<li class='warn'>{_e(e)}</li>\n"
        s += "</ul>\n"

    return s + "<hr>\n"


# ── Services ──────────────────────────────────────────────────────────────────

def _services_html(data: ServicesData | None) -> str:
    s = "<h2>⚙ Services</h2>\n"
    if data is None:
        return s + _NOT_SCANNED

    if data.services:
        s += "<table><thead><tr><th>Service</th><th>Display Name</th><th>Status</th><th>Startup</th><th>Purpose</th></tr></thead><tbody>\n"
        for svc in data.services:
            ok = svc.status == "Running"
            st_html = (f'<span class="ok">✓ {_e(svc.status)}</span>' if ok
                       else f'<span class="err">✕ {_e(svc.status)}</span>' if svc.status == "Stopped"
                       else f'<span class="warn">● {_e(svc.status)}</span>')
            s += (f"<tr><td><strong>{_e(svc.name)}</strong></td><td class='muted'>{_e(svc.display_name or '—')}</td>"
                  f"<td>{st_html}</td><td class='muted'>{_e(svc.start_type or '—')}</td>"
                  f"<td>{_e(svc.required_for)}</td></tr>\n")
        s += "</tbody></table>\n"

    if data.errors:
        s += "<h3>⚠ Scan Warnings</h3>\n<ul>\n"
        for e in data.errors:
            s += f"<li class='warn'>{_e(e)}</li>\n"
        s += "</ul>\n"

    return s + "<hr>\n"


# ── Printers ──────────────────────────────────────────────────────────────────

def _printers_html(data: PrintersData | None) -> str:
    s = "<h2>🖨 Printers</h2>\n"
    if data is None:
        return s + _NOT_SCANNED

    if data.printers:
        s += f"<h3>Installed Printers ({len(data.printers)})</h3>\n"
        s += "<table><thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Driver</th><th>Default</th><th>Jobs</th></tr></thead><tbody>\n"
        for p in data.printers:
            ok = p.status == "Normal"
            st_html = (f'<span class="ok">✓ {_e(p.status)}</span>' if ok
                       else f'<span class="err">✕ {_e(p.status)}</span>')
            default_html = '<span class="warn">★</span>' if p.is_default else ""
            jobs_html = (f'<span class="warn">{p.job_count}</span>' if p.job_count > 0
                         else '<span class="muted">0</span>')
            s += (f"<tr><td><strong>{_e(p.name)}</strong></td><td class='muted'>{_e(p.printer_type or '—')}</td>"
                  f"<td>{st_html}</td><td class='muted'>{_e(p.driver_name or '—')}</td>"
                  f"<td>{default_html}</td><td>{jobs_html}</td></tr>\n")
        s += "</tbody></table>\n"

    if data.print_jobs:
        s += f"<h3>Active Print Jobs ({len(data.print_jobs)})</h3>\n"
        s += "<table><thead><tr><th>ID</th><th>Printer</th><th>Document</th><th>User</th><th>Pages</th><th>Status</th></tr></thead><tbody>\n"
        for j in data.print_jobs:
            s += (f"<tr><td class='muted'>{j.job_id}</td><td>{_e(j.printer_name)}</td>"
                  f"<td>{_e(j.document_name)}</td><td class='muted'>{_e(j.user_name)}</td>"
                  f"<td class='muted'>{_e(j.total_pages or '—')}</td>"
                  f"<td class='warn'>{_e(j.status)}</td></tr>\n")
        s += "</tbody></table>\n"

    if data.errors:
        s += "<h3>⚠ Scan Warnings</h3>\n<ul>\n"
        for e in data.errors:
            s += f"<li class='warn'>{_e(e)}</li>\n"
        s += "</ul>\n"

    return s + "<hr>\n"
