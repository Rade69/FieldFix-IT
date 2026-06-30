"""Tests for DecisionEngine v1 — one test per major rule."""

import pytest

from app.core.decision_engine import DecisionEngine
from app.core.issue import Issue
from app.core.risk_level import RiskLevel
from app.modules.network.models import (
    AdapterInfo, ArpEntry, GatewayInfo, IPAddressInfo, NetworkData, NetworkProfile,
)
from app.modules.printers.models import PrinterInfo, PrintJob, PrintersData
from app.modules.services.models import ServiceInfo, ServicesData
from app.modules.smb.models import (
    PortCheckResult, SmbClientConfig, SmbData, SmbServerConfig,
)
from app.reports.models import ScanReport

_DE = DecisionEngine()


def _net(**kw) -> NetworkData:
    defaults = dict(
        hostname="TEST-PC",
        adapters=(AdapterInfo(name="Eth", description="NIC", status="Up"),),
        gateways=(GatewayInfo(interface_alias="Eth", next_hop="192.168.1.1"),),
        gateway_reachable=True,
        ip_addresses=(IPAddressInfo(interface_alias="Eth", ip_address="192.168.1.100", prefix_length=24),),
        profiles=(NetworkProfile(name="Home", interface_alias="Eth", category="Private"),),
        arp_entries=(),
    )
    defaults.update(kw)
    return NetworkData(**defaults)


def _smb(**kw) -> SmbData:
    defaults = dict(
        server_config=SmbServerConfig(smb1_enabled=False, smb2_enabled=True,
                                      require_security_signature=False, enable_security_signature=True),
        client_config=SmbClientConfig(smb1_enabled=False, require_security_signature=False,
                                      enable_security_signature=True, enable_insecure_guest_logons=False),
    )
    defaults.update(kw)
    return SmbData(**defaults)


def _svc(*items: ServiceInfo) -> ServicesData:
    return ServicesData(services=items)


def _report(**kw) -> ScanReport:
    return ScanReport(generated_at="2026-06-30T12:00:00", **kw)


def _issue_ids(issues: tuple[Issue, ...]) -> list[str]:
    return [i.id for i in issues]


# ── Empty report ──────────────────────────────────────────────────────────────

def test_empty_report_returns_no_issues():
    assert _DE.analyze(_report()) == ()


def test_returns_tuple():
    assert isinstance(_DE.analyze(_report()), tuple)


# ── Network rules ─────────────────────────────────────────────────────────────

def test_no_adapters_is_high():
    report = _report(network=_net(adapters=()))
    ids = _issue_ids(_DE.analyze(report))
    assert "NO_ACTIVE_ADAPTERS" in ids


def test_no_gateway_is_high():
    report = _report(network=_net(gateways=()))
    ids = _issue_ids(_DE.analyze(report))
    assert "NO_GATEWAY" in ids


def test_gateway_unreachable_is_high():
    report = _report(network=_net(gateway_reachable=False))
    ids = _issue_ids(_DE.analyze(report))
    assert "GATEWAY_UNREACHABLE" in ids


def test_gateway_reachable_no_issue():
    report = _report(network=_net(gateway_reachable=True))
    ids = _issue_ids(_DE.analyze(report))
    assert "GATEWAY_UNREACHABLE" not in ids


def test_public_profile_is_medium():
    net = _net(profiles=(NetworkProfile(name="Net", interface_alias="Eth", category="Public"),))
    report = _report(network=net)
    issues = _DE.analyze(report)
    pub = [i for i in issues if i.id == "PUBLIC_NETWORK_PROFILE"]
    assert pub and pub[0].severity == RiskLevel.MEDIUM


def test_private_profile_no_issue():
    report = _report(network=_net())
    ids = _issue_ids(_DE.analyze(report))
    assert "PUBLIC_NETWORK_PROFILE" not in ids


# ── SMB rules ────────────────────────────────────────────────────────────────

def test_smb1_enabled_server_is_high():
    sc = SmbServerConfig(smb1_enabled=True, smb2_enabled=True,
                         require_security_signature=False, enable_security_signature=True)
    report = _report(smb=_smb(server_config=sc))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "SMB1_ENABLED_SERVER"]
    assert match and match[0].severity == RiskLevel.HIGH


def test_smb1_disabled_server_no_issue():
    report = _report(smb=_smb())
    ids = _issue_ids(_DE.analyze(report))
    assert "SMB1_ENABLED_SERVER" not in ids


def test_smb1_enabled_client_is_medium():
    cc = SmbClientConfig(smb1_enabled=True, require_security_signature=False,
                         enable_security_signature=True, enable_insecure_guest_logons=False)
    report = _report(smb=_smb(client_config=cc))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "SMB1_ENABLED_CLIENT"]
    assert match and match[0].severity == RiskLevel.MEDIUM


def test_guest_logons_enabled_is_medium():
    cc = SmbClientConfig(smb1_enabled=False, require_security_signature=False,
                         enable_security_signature=True, enable_insecure_guest_logons=True)
    report = _report(smb=_smb(client_config=cc))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "GUEST_LOGONS_ENABLED"]
    assert match and match[0].severity == RiskLevel.MEDIUM


def test_port_445_closed_is_high():
    port = PortCheckResult(target_ip="192.168.1.5", port=445, reachable=False)
    report = _report(smb=_smb(port_445=port))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "PORT_445_CLOSED"]
    assert match and match[0].severity == RiskLevel.HIGH


def test_net_view_6118_is_medium():
    report = _report(smb=_smb(net_view_error_code=6118))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "NET_VIEW_ERROR_6118"]
    assert match and match[0].severity == RiskLevel.MEDIUM


def test_net_view_1272_is_medium():
    report = _report(smb=_smb(net_view_error_code=1272))
    ids = _issue_ids(_DE.analyze(report))
    assert "NET_VIEW_ERROR_1272" in ids


def test_net_view_53_is_high():
    report = _report(smb=_smb(net_view_error_code=53))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "NET_VIEW_ERROR_53"]
    assert match and match[0].severity == RiskLevel.HIGH


# ── Combined rules ────────────────────────────────────────────────────────────

def test_gateway_ok_port_445_fail_is_firewall_issue():
    port = PortCheckResult(target_ip="192.168.1.5", port=445, reachable=False)
    report = _report(network=_net(gateway_reachable=True), smb=_smb(port_445=port))
    ids = _issue_ids(_DE.analyze(report))
    assert "FIREWALL_PORT_445_BLOCKED" in ids


def test_net_view_6118_port_445_open_is_browsing_problem():
    port = PortCheckResult(target_ip="192.168.1.5", port=445, reachable=True)
    report = _report(
        network=_net(),
        smb=_smb(net_view_error_code=6118, port_445=port),
    )
    ids = _issue_ids(_DE.analyze(report))
    assert "BROWSING_PROBLEM_NOT_SMB" in ids


def test_no_combined_issues_when_all_ok():
    port = PortCheckResult(target_ip="192.168.1.5", port=445, reachable=True)
    report = _report(network=_net(), smb=_smb(port_445=port))
    ids = _issue_ids(_DE.analyze(report))
    assert "FIREWALL_PORT_445_BLOCKED" not in ids
    assert "BROWSING_PROBLEM_NOT_SMB" not in ids


# ── Services rules ────────────────────────────────────────────────────────────

def test_lanmanserver_stopped_is_high():
    svc = ServiceInfo(name="LanmanServer", status="Stopped", display_name="Server")
    report = _report(services=_svc(svc))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "SERVICE_STOPPED_LANMANSERVER"]
    assert match and match[0].severity == RiskLevel.HIGH


def test_lanmanworkstation_stopped_is_high():
    svc = ServiceInfo(name="LanmanWorkstation", status="Stopped")
    report = _report(services=_svc(svc))
    ids = _issue_ids(_DE.analyze(report))
    assert "SERVICE_STOPPED_LANMANWORKSTATION" in ids


def test_spooler_stopped_is_medium():
    svc = ServiceInfo(name="Spooler", status="Stopped")
    report = _report(services=_svc(svc))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "SERVICE_STOPPED_SPOOLER"]
    assert match and match[0].severity == RiskLevel.MEDIUM


def test_fdrespub_stopped_is_low():
    svc = ServiceInfo(name="FDResPub", status="Stopped")
    report = _report(services=_svc(svc))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "SERVICE_STOPPED_FDRESPUB"]
    assert match and match[0].severity == RiskLevel.LOW


def test_running_services_no_issues():
    svcs = (
        ServiceInfo(name="LanmanServer", status="Running"),
        ServiceInfo(name="Spooler", status="Running"),
    )
    report = _report(services=ServicesData(services=svcs))
    assert _DE.analyze(report) == ()


# ── Printers rules ────────────────────────────────────────────────────────────

def test_printer_error_is_high():
    prn = PrinterInfo(name="HP LaserJet", status="Error")
    report = _report(printers=PrintersData(printers=(prn,)))
    issues = _DE.analyze(report)
    assert any(i.severity == RiskLevel.HIGH for i in issues)


def test_printer_offline_is_high():
    prn = PrinterInfo(name="Canon", status="Offline")
    report = _report(printers=PrintersData(printers=(prn,)))
    issues = _DE.analyze(report)
    assert any("Canon" in i.title for i in issues)


def test_printer_normal_no_issue():
    prn = PrinterInfo(name="HP LaserJet", status="Normal")
    report = _report(printers=PrintersData(printers=(prn,)))
    assert _DE.analyze(report) == ()


def test_stuck_print_job_is_low():
    job = PrintJob(job_id=7, printer_name="HP", document_name="doc.pdf",
                   user_name="radovan", status="Error")
    report = _report(printers=PrintersData(print_jobs=(job,)))
    issues = _DE.analyze(report)
    match = [i for i in issues if i.id == "PRINT_JOB_ERROR_7"]
    assert match and match[0].severity == RiskLevel.LOW


# ── Ordering ──────────────────────────────────────────────────────────────────

def test_issues_sorted_high_first():
    port = PortCheckResult(target_ip="192.168.1.5", port=445, reachable=False)
    sc = SmbServerConfig(smb1_enabled=True, smb2_enabled=True,
                         require_security_signature=False, enable_security_signature=True)
    cc = SmbClientConfig(smb1_enabled=False, require_security_signature=False,
                         enable_security_signature=True, enable_insecure_guest_logons=True)
    report = _report(
        network=_net(gateway_reachable=True),
        smb=_smb(server_config=sc, client_config=cc, port_445=port),
    )
    issues = _DE.analyze(report)
    severities = [i.severity for i in issues]
    assert severities == sorted(severities, reverse=True)
