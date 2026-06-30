"""Tests for JSON, Markdown, and HTML report writers."""

import json

from app.modules.network.models import NetworkData, AdapterInfo, GatewayInfo, IPAddressInfo
from app.modules.printers.models import PrinterInfo, PrintersData
from app.modules.services.models import ServiceInfo, ServicesData
from app.modules.smb.models import SmbClientConfig, SmbData, SmbServerConfig, SmbShare
from app.reports.html_report import write_html
from app.reports.json_report import write_json
from app.reports.markdown_report import write_markdown
from app.reports.models import ScanReport


def _minimal_report(**kwargs) -> ScanReport:
    return ScanReport(generated_at="2026-06-30T15:00:00", hostname="TEST-PC", **kwargs)


def _network_data() -> NetworkData:
    return NetworkData(
        hostname="TEST-PC",
        adapters=(AdapterInfo(name="Ethernet", description="Intel NIC", status="Up", link_speed_bps=1_000_000_000, mac_address="AA:BB:CC:DD:EE:FF"),),
        ip_addresses=(IPAddressInfo(interface_alias="Ethernet", ip_address="192.168.1.100", prefix_length=24),),
        gateways=(GatewayInfo(interface_alias="Ethernet", next_hop="192.168.1.1"),),
        gateway_reachable=True,
        scan_duration_ms=250.0,
    )


def _services_data() -> ServicesData:
    return ServicesData(
        services=(
            ServiceInfo(name="LanmanServer", display_name="Server", status="Running", start_type="Automatic", required_for="File sharing"),
            ServiceInfo(name="Spooler", display_name="Print Spooler", status="Stopped", start_type="Manual", required_for="Printing"),
        ),
        scan_duration_ms=80.0,
    )


def _printers_data() -> PrintersData:
    return PrintersData(
        printers=(
            PrinterInfo(name="HP LaserJet", driver_name="HP PCL6", port_name="IP_192.168.1.10", printer_type="Connection", status="Normal", is_default=True),
        ),
    )


def _smb_data() -> SmbData:
    return SmbData(
        server_config=SmbServerConfig(smb1_enabled=False, smb2_enabled=True,
                                      require_security_signature=False, enable_security_signature=True),
        client_config=SmbClientConfig(smb1_enabled=False, require_security_signature=False,
                                      enable_security_signature=True, enable_insecure_guest_logons=False),
        shares=(SmbShare(name="Public", path="C:\\Public", description="Public share", share_type="Disk"),),
    )


# ── JSON ──────────────────────────────────────────────────────────────────────

class TestJsonReport:
    def test_returns_valid_json(self):
        report = _minimal_report()
        result = write_json(report)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_generated_at_present(self):
        result = write_json(_minimal_report())
        parsed = json.loads(result)
        assert parsed["generated_at"] == "2026-06-30T15:00:00"

    def test_hostname_present(self):
        result = write_json(_minimal_report())
        assert "TEST-PC" in result

    def test_none_sections_are_null(self):
        parsed = json.loads(write_json(_minimal_report()))
        assert parsed["network"] is None
        assert parsed["smb"] is None
        assert parsed["services"] is None
        assert parsed["printers"] is None

    def test_network_section_serialized(self):
        report = _minimal_report(network=_network_data())
        parsed = json.loads(write_json(report))
        assert parsed["network"]["hostname"] == "TEST-PC"
        assert len(parsed["network"]["adapters"]) == 1

    def test_services_section_serialized(self):
        report = _minimal_report(services=_services_data())
        parsed = json.loads(write_json(report))
        assert len(parsed["services"]["services"]) == 2

    def test_tuples_become_arrays(self):
        report = _minimal_report(services=_services_data())
        parsed = json.loads(write_json(report))
        assert isinstance(parsed["services"]["services"], list)

    def test_all_sections(self):
        report = _minimal_report(
            network=_network_data(), smb=_smb_data(),
            services=_services_data(), printers=_printers_data(),
        )
        parsed = json.loads(write_json(report))
        assert parsed["network"] is not None
        assert parsed["smb"] is not None
        assert parsed["services"] is not None
        assert parsed["printers"] is not None


# ── Markdown ──────────────────────────────────────────────────────────────────

class TestMarkdownReport:
    def test_returns_string(self):
        assert isinstance(write_markdown(_minimal_report()), str)

    def test_contains_title(self):
        assert "# FieldFix IT" in write_markdown(_minimal_report())

    def test_contains_hostname(self):
        assert "TEST-PC" in write_markdown(_minimal_report())

    def test_contains_generated_at(self):
        assert "2026-06-30T15:00:00" in write_markdown(_minimal_report())

    def test_not_scanned_for_missing_sections(self):
        result = write_markdown(_minimal_report())
        assert "Not scanned" in result

    def test_network_section_present(self):
        report = _minimal_report(network=_network_data())
        result = write_markdown(report)
        assert "## 🌐 Network" in result
        assert "192.168.1.100" in result
        assert "✓ Reachable" in result

    def test_services_table_present(self):
        report = _minimal_report(services=_services_data())
        result = write_markdown(report)
        assert "LanmanServer" in result
        assert "Spooler" in result
        assert "✓ Running" in result
        assert "✕ Stopped" in result

    def test_smb_section_smb1_disabled_shown(self):
        report = _minimal_report(smb=_smb_data(), smb_target_ip="192.168.1.50")
        result = write_markdown(report)
        assert "Disabled (good)" in result
        assert "192.168.1.50" in result

    def test_printers_section_default_marked(self):
        report = _minimal_report(printers=_printers_data())
        result = write_markdown(report)
        assert "HP LaserJet" in result
        assert "★" in result

    def test_all_section_headers_present(self):
        report = _minimal_report(
            network=_network_data(), smb=_smb_data(),
            services=_services_data(), printers=_printers_data(),
        )
        result = write_markdown(report)
        assert "## 🌐 Network" in result
        assert "## 📁 SMB" in result
        assert "## ⚙ Services" in result
        assert "## 🖨 Printers" in result


# ── HTML ──────────────────────────────────────────────────────────────────────

class TestHtmlReport:
    def test_returns_string(self):
        assert isinstance(write_html(_minimal_report()), str)

    def test_valid_html_doctype(self):
        assert write_html(_minimal_report()).startswith("<!DOCTYPE html>")

    def test_contains_title(self):
        assert "FieldFix IT" in write_html(_minimal_report())

    def test_contains_hostname(self):
        assert "TEST-PC" in write_html(_minimal_report())

    def test_html_escaping_in_values(self):
        report = ScanReport(generated_at="2026-06-30", hostname="<script>alert(1)</script>")
        result = write_html(report)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_not_scanned_for_missing_sections(self):
        assert "Not scanned" in write_html(_minimal_report())

    def test_network_section_present(self):
        report = _minimal_report(network=_network_data())
        result = write_html(report)
        assert "192.168.1.100" in result
        assert "Reachable" in result

    def test_services_status_colored(self):
        report = _minimal_report(services=_services_data())
        result = write_html(report)
        assert 'class="ok"' in result
        assert 'class="err"' in result

    def test_smb1_disabled_good_shown(self):
        report = _minimal_report(smb=_smb_data())
        result = write_html(report)
        assert "Disabled (good)" in result

    def test_default_printer_starred(self):
        report = _minimal_report(printers=_printers_data())
        result = write_html(report)
        assert "★" in result

    def test_inline_css_present(self):
        result = write_html(_minimal_report())
        assert "<style>" in result
        assert "font-family" in result

    def test_footer_present(self):
        result = write_html(_minimal_report())
        assert "<footer>" in result
