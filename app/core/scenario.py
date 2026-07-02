"""Scenario definitions and check functions for guided diagnostics.

A Scenario bundles: which issue IDs are relevant, human-readable check
labels, and a function that maps a ScanResult to a list of CheckItems
(pass/fail with optional fix pointer).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.scan_session import ScanResult


@dataclass(frozen=True)
class CheckItem:
    label: str
    passed: bool
    detail: str = ""
    fix_id: str = ""        # matches FixAction.id in fix_center_page._AVAILABLE_FIXES
    group: str = ""         # display group header in ResultsPanel


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    description: str
    icon: str
    tip: str
    scan_modules: tuple[str, ...]   # "network", "smb", "services"
    check_fn_name: str              # name of the check function below


# ── Built-in scenarios ────────────────────────────────────────────────────────

CONNECT_TWO_PCS = Scenario(
    id="connect_two_pcs",
    title="Connect two Windows PCs",
    description=(
        "Diagnoses everything needed for file sharing and network discovery "
        "between two Windows computers on the same local network.\n\n"
        "Checks: network profile, SMB protocol, firewall rules, Server service, "
        "and Network Discovery."
    ),
    icon="🖥",
    tip="Enter the IP of the other PC for a full check (port 445 reachability).",
    scan_modules=("network", "smb", "services"),
    check_fn_name="check_connect_two_pcs",
)

ADD_NETWORK_PRINTER = Scenario(
    id="add_network_printer",
    title="Add Network Printer",
    description=(
        "Checks prerequisites and installs a network printer already on your network.\n\n"
        "Scans: Print Spooler, Network Discovery, firewall rules, and printer reachability. "
        "If everything looks good, installs the printer on this PC with one click."
    ),
    icon="🖨",
    tip="Enter the printer's IP address to check connectivity and install it on this PC.",
    scan_modules=("network", "services", "printers"),
    check_fn_name="check_add_network_printer",
)

FIX_PRINTER_PROBLEMS = Scenario(
    id="fix_printer_problems",
    title="Fix Printer Problems",
    description=(
        "Diagnoses why an installed printer isn't working and fixes common issues.\n\n"
        "Checks: Print Spooler status, printer online/offline, stuck print queue, "
        "and network reachability. Fixes applied directly here — no Fix Center needed."
    ),
    icon="🔧",
    tip="Select the printer that isn't working from the list below.",
    scan_modules=("services", "printers", "network"),
    check_fn_name="check_fix_printer_problems",
)

ALL_SCENARIOS: tuple[Scenario, ...] = (CONNECT_TWO_PCS, ADD_NETWORK_PRINTER, FIX_PRINTER_PROBLEMS)


# ── Check functions ───────────────────────────────────────────────────────────

def check_connect_two_pcs(result: ScanResult, target_ip: str = "") -> list[CheckItem]:
    """Return an ordered checklist for the 'Connect two Windows PCs' scenario."""
    issue_ids = {i.id for i in result.issues}
    net  = result.report.network
    smb  = result.report.smb
    svc  = result.report.services

    items: list[CheckItem] = []

    # ── Network layer ─────────────────────────────────────────────────────────

    adapter_ok = bool(net and net.adapters)
    items.append(CheckItem(
        label="Network adapter active",
        passed=adapter_ok,
        detail="" if adapter_ok else "No active network adapter found — check cable or Wi-Fi.",
        group="Network",
    ))

    profile_ok = "PUBLIC_NETWORK_PROFILE" not in issue_ids
    if net and net.profiles:
        pub = [p.interface_alias for p in net.profiles if p.category == "Public"]
        detail = f"Profile is Public on: {', '.join(pub)} — blocks file sharing." if pub else ""
    else:
        detail = ""
    items.append(CheckItem(
        label="Network profile is Private",
        passed=profile_ok,
        detail=detail,
        fix_id="" if profile_ok else "SET_NETWORK_PRIVATE",
        group="Network",
    ))

    # ── Sharing layer ─────────────────────────────────────────────────────────

    server_ok = "SERVICE_STOPPED_LANMANSERVER" not in issue_ids
    items.append(CheckItem(
        label="Server service running (LanmanServer)",
        passed=server_ok,
        detail="" if server_ok else "Server service is stopped — shared folders are unavailable.",
        fix_id="" if server_ok else "START_LANMANSERVER",
        group="Sharing",
    ))

    workstation_ok = "SERVICE_STOPPED_LANMANWORKSTATION" not in issue_ids
    items.append(CheckItem(
        label="Workstation service running (LanmanWorkstation)",
        passed=workstation_ok,
        detail="" if workstation_ok else "Workstation service is stopped — cannot connect to remote shares.",
        fix_id="" if workstation_ok else "START_LANMANWORKSTATION",
        group="Sharing",
    ))

    smb1_ok = "SMB1_ENABLED_SERVER" not in issue_ids
    items.append(CheckItem(
        label="SMB1 disabled (security)",
        passed=smb1_ok,
        detail="" if smb1_ok else "SMB1 is enabled — legacy protocol vulnerable to EternalBlue/WannaCry.",
        fix_id="" if smb1_ok else "DISABLE_SMB1",
        group="Sharing",
    ))

    # ── Firewall / connectivity layer ─────────────────────────────────────────

    fp_sharing_ok = (
        "PORT_445_CLOSED" not in issue_ids
        and "FIREWALL_PORT_445_BLOCKED" not in issue_ids
    )
    if target_ip:
        detail_fp = (
            "" if fp_sharing_ok
            else f"Port 445 not reachable on {target_ip} — firewall or Server service on target."
        )
    else:
        detail_fp = "" if fp_sharing_ok else "SMB port issue detected on this PC."
    items.append(CheckItem(
        label=f"File and Printer Sharing reachable{f' ({target_ip})' if target_ip else ''}",
        passed=fp_sharing_ok or not target_ip,
        detail=detail_fp,
        fix_id="" if fp_sharing_ok else "ENABLE_FILE_PRINTER_SHARING",
        group="Firewall & Discovery",
    ))

    # ── Discovery layer ───────────────────────────────────────────────────────

    fdrespub_ok = "SERVICE_STOPPED_FDRESPUB" not in issue_ids
    items.append(CheckItem(
        label="FDResPub service running (visible in Network)",
        passed=fdrespub_ok,
        detail="" if fdrespub_ok else "This PC is not visible to other devices in Network Discovery.",
        fix_id="" if fdrespub_ok else "START_FDRESPUB",
        group="Firewall & Discovery",
    ))

    nd_blocked = "BROWSING_PROBLEM_NOT_SMB" in issue_ids or "NET_VIEW_ERROR_6118" in issue_ids
    items.append(CheckItem(
        label="Network Discovery enabled",
        passed=not nd_blocked,
        detail="" if not nd_blocked else "Network Discovery is blocked — computers cannot find each other by name.",
        fix_id="" if not nd_blocked else "ENABLE_NETWORK_DISCOVERY",
        group="Firewall & Discovery",
    ))

    return items


@dataclass(frozen=True)
class RemoteStep:
    label: str
    manual: str     # plain-language instruction
    ps_cmd: str     # PowerShell command they can paste (as Admin)


def remote_checklist_connect_two_pcs() -> list[RemoteStep]:
    """Steps the user must apply manually on the OTHER PC."""
    return [
        RemoteStep(
            label="Set Network Profile to Private",
            manual=(
                "Open Settings → Network & Internet → your connection → Properties "
                "→ set Network profile to Private."
            ),
            ps_cmd=(
                "Get-NetConnectionProfile | "
                "Where-Object {$_.NetworkCategory -eq 'Public'} | "
                "Set-NetConnectionProfile -NetworkCategory Private"
            ),
        ),
        RemoteStep(
            label="Enable File and Printer Sharing (Firewall)",
            manual=(
                "Control Panel → Windows Defender Firewall → "
                "Allow an app → check 'File and Printer Sharing'."
            ),
            ps_cmd='netsh advfirewall firewall set rule group="file and printer sharing" new enable=Yes',
        ),
        RemoteStep(
            label="Enable Network Discovery (Firewall)",
            manual=(
                "Control Panel → Windows Defender Firewall → "
                "Allow an app → check 'Network Discovery'."
            ),
            ps_cmd='netsh advfirewall firewall set rule group="network discovery" new enable=Yes',
        ),
        RemoteStep(
            label="Start Server service (LanmanServer)",
            manual="Press Win+R → services.msc → find 'Server' → Start, set Startup to Automatic.",
            ps_cmd="Start-Service LanmanServer; Set-Service LanmanServer -StartupType Automatic",
        ),
        RemoteStep(
            label="Start FDResPub service (Network Discovery visibility)",
            manual="Press Win+R → services.msc → find 'Function Discovery Resource Publication' → Start.",
            ps_cmd="Start-Service FDResPub",
        ),
    ]


def check_add_network_printer(result: ScanResult, target_ip: str = "") -> list[CheckItem]:
    """Return an ordered checklist for the 'Add Network Printer' scenario."""
    issue_ids = {i.id for i in result.issues}
    net = result.report.network
    svc = result.report.services
    prn = result.report.printers

    items: list[CheckItem] = []

    # ── Spooler layer ─────────────────────────────────────────────────────────

    spooler_ok = "SERVICE_STOPPED_SPOOLER" not in issue_ids
    items.append(CheckItem(
        label="Print Spooler service running",
        passed=spooler_ok,
        detail="" if spooler_ok else "Print Spooler is stopped — no printing is possible.",
        fix_id="" if spooler_ok else "START_PRINT_SPOOLER",
        group="Spooler",
    ))

    # ── Network layer ─────────────────────────────────────────────────────────

    profile_ok = "PUBLIC_NETWORK_PROFILE" not in issue_ids
    items.append(CheckItem(
        label="Network profile is Private",
        passed=profile_ok,
        detail="" if profile_ok else "Public profile blocks Network Discovery — printer won't be found automatically.",
        fix_id="" if profile_ok else "SET_NETWORK_PRIVATE",
        group="Network",
    ))

    # ── Discovery layer ───────────────────────────────────────────────────────

    fdrespub_ok = "SERVICE_STOPPED_FDRESPUB" not in issue_ids
    items.append(CheckItem(
        label="FDResPub service running (printer discovery)",
        passed=fdrespub_ok,
        detail="" if fdrespub_ok else "FDResPub stopped — Windows cannot discover network printers automatically.",
        fix_id="" if fdrespub_ok else "START_FDRESPUB",
        group="Discovery",
    ))

    nd_blocked = "BROWSING_PROBLEM_NOT_SMB" in issue_ids or "NET_VIEW_ERROR_6118" in issue_ids
    items.append(CheckItem(
        label="Network Discovery enabled (firewall)",
        passed=not nd_blocked,
        detail="" if not nd_blocked else "Network Discovery is blocked — printers won't appear in 'Add a printer' wizard.",
        fix_id="" if not nd_blocked else "ENABLE_NETWORK_DISCOVERY",
        group="Discovery",
    ))

    items.append(CheckItem(
        label="File and Printer Sharing enabled (firewall)",
        passed="FIREWALL_PORT_445_BLOCKED" not in issue_ids,
        detail="",
        fix_id="ENABLE_FILE_PRINTER_SHARING",
        group="Discovery",
    ))

    # ── Printer IP reachability ───────────────────────────────────────────────

    if target_ip:
        arp_ips = {e.ip_address for e in net.arp_entries} if net else set()
        printer_in_arp = target_ip in arp_ips

        # Check if already installed with that IP
        installed_ips = {p.ip_address for p in prn.printers if p.ip_address} if prn else set()
        already_installed = target_ip in installed_ips

        if already_installed:
            items.append(CheckItem(
                label=f"Printer {target_ip} — already installed on this PC",
                passed=True,
                detail="A printer with this IP is already configured. Check its status in Printers page.",
                group="Printer",
            ))
        else:
            items.append(CheckItem(
                label=f"Printer visible on network ({target_ip})",
                passed=printer_in_arp,
                detail="" if printer_in_arp
                else f"{target_ip} not found in ARP table — printer may be off, wrong IP, or on a different subnet.",
                group="Printer",
            ))

    return items


def remote_checklist_add_network_printer() -> list[RemoteStep]:
    """Steps the user must verify on the printer side."""
    return [
        RemoteStep(
            label="Confirm printer is powered on and network-connected",
            manual="Check that the printer's network indicator light is on (Ethernet cable or Wi-Fi connected).",
            ps_cmd="# No PowerShell needed — physical check on the printer.",
        ),
        RemoteStep(
            label="Find the printer's IP address",
            manual=(
                "On the printer: print a Configuration/Test page (usually via a menu button). "
                "The IP address is printed there. Alternatively check your router's connected devices list."
            ),
            ps_cmd="# On this PC, check the ARP table: arp -a",
        ),
        RemoteStep(
            label="Verify printer is on the same subnet",
            manual=(
                "The printer IP (e.g. 192.168.1.x) must be on the same subnet as this PC. "
                "Compare the first three octets — they must match."
            ),
            ps_cmd="ipconfig | findstr IPv4",
        ),
        RemoteStep(
            label="Check printer's web interface",
            manual=(
                "Open a browser and go to http://[printer-ip]. "
                "If you see a printer settings page, the printer is reachable. "
                "Make sure 'Network Printing' or 'IPP' is enabled in its settings."
            ),
            ps_cmd="# In browser: http://[printer-ip]",
        ),
        RemoteStep(
            label="Ping the printer from this PC",
            manual="Confirm the printer responds to ping before trying to add it.",
            ps_cmd="ping [printer-ip] -n 4",
        ),
    ]


def check_fix_printer_problems(result: ScanResult, target_name: str = "") -> list[CheckItem]:
    """Return an ordered checklist for the 'Fix Printer Problems' scenario."""
    issue_ids = {i.id for i in result.issues}
    prn  = result.report.printers
    net  = result.report.network

    items: list[CheckItem] = []

    spooler_ok = "SERVICE_STOPPED_SPOOLER" not in issue_ids
    items.append(CheckItem(
        label="Print Spooler service running",
        passed=spooler_ok,
        detail="" if spooler_ok else "Spooler is stopped — no printer will work until it is restarted.",
        fix_id="" if spooler_ok else "START_PRINT_SPOOLER",
        group="Spooler",
    ))

    if not target_name or not prn:
        return items

    printer = next((p for p in prn.printers if p.name == target_name), None)
    if not printer:
        return items

    # ── Online / paused / error ───────────────────────────────────────────────

    status_lo = printer.status.lower()
    is_offline = any(s in status_lo for s in ("offline", "paused", "error"))
    items.append(CheckItem(
        label="Printer is online",
        passed=not is_offline,
        detail="" if not is_offline
        else f"Status: {printer.status} — printer is unreachable, paused, or in error state.",
        group="Printer Status",
    ))

    # ── Print queue ───────────────────────────────────────────────────────────

    queue_ok = printer.job_count == 0
    items.append(CheckItem(
        label="Print queue is clear",
        passed=queue_ok,
        detail="" if queue_ok else f"{printer.job_count} job(s) stuck in the queue.",
        group="Print Queue",
    ))

    # ── Network reachability (TCP/IP printers only) ───────────────────────────

    if printer.ip_address:
        arp_ips = {e.ip_address for e in net.arp_entries} if net else set()
        reachable = printer.ip_address in arp_ips
        items.append(CheckItem(
            label=f"Printer reachable on network ({printer.ip_address})",
            passed=reachable,
            detail="" if reachable
            else f"{printer.ip_address} not responding — printer may be off or its IP changed.",
            group="Network",
        ))

    return items


def run_checks(
    scenario: Scenario,
    result: ScanResult,
    target_ip: str = "",
    target_name: str = "",
) -> list[CheckItem]:
    """Dispatch to the correct check function for the given scenario."""
    if scenario.check_fn_name == "check_connect_two_pcs":
        return check_connect_two_pcs(result, target_ip)
    if scenario.check_fn_name == "check_add_network_printer":
        return check_add_network_printer(result, target_ip)
    if scenario.check_fn_name == "check_fix_printer_problems":
        return check_fix_printer_problems(result, target_name)
    return []


def run_remote_checklist(scenario: Scenario) -> list[RemoteStep]:
    """Return steps the user must apply manually on the remote device."""
    if scenario.check_fn_name == "check_connect_two_pcs":
        return remote_checklist_connect_two_pcs()
    if scenario.check_fn_name == "check_add_network_printer":
        return remote_checklist_add_network_printer()
    return []
