from app.core.issue import Issue
from app.core.risk_level import RiskLevel
from app.core.scan_session import ScanResult
from app.gui.dashboard import _build_summary
from app.modules.network.models import ArpEntry, GatewayInfo, IPAddressInfo, NetworkData
from app.modules.printers.models import PrinterInfo, PrintersData
from app.reports.models import ScanReport


def test_build_summary_counts_scan_objects_and_suggests_step():
    network = NetworkData(
        hostname="TEST-PC",
        ip_addresses=(IPAddressInfo("Ethernet", "192.168.1.10"),),
        gateways=(GatewayInfo("Ethernet", "192.168.1.1"),),
        arp_entries=(
            ArpEntry("Ethernet", "192.168.1.20", "AA-BB-CC", "Reachable"),
            ArpEntry("Ethernet", "224.0.0.252", "01-00-5E-00-00-FC", "Permanent"),
            ArpEntry("Ethernet", "192.168.1.255", "FF-FF-FF-FF-FF-FF", "Permanent"),
        ),
    )
    printers = PrintersData(printers=(
        PrinterInfo(name="Canon", status="Normal"),
        PrinterInfo(name="HP", status="Offline"),
    ))
    issue = Issue(
        id="FW",
        title="Firewall issue",
        severity=RiskLevel.HIGH,
        related_module="firewall",
    )
    result = ScanResult(
        report=ScanReport(
            generated_at="2026-07-01T12:00:00",
            network=network,
            printers=printers,
        ),
        issues=(issue,),
        scanned_at="2026-07-01T12:00:00",
    )

    assert _build_summary(result) == (
        "Found: 1 gateway, 2 printers, 1 LAN device. "
        "Issues: 1. Suggested: Check firewall rules."
    )
