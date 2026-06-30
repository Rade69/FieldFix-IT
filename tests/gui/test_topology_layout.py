from app.gui.pages.topology_page import build_nodes, compute_positions
from app.modules.network.models import ArpEntry, GatewayInfo, IPAddressInfo, NetworkData
from app.modules.printers.models import PrinterInfo, PrintersData


def _network(
    hostname: str = "NOVI",
    ips: tuple[IPAddressInfo, ...] = (IPAddressInfo("Ethernet", "192.168.1.10"),),
    gateways: tuple[GatewayInfo, ...] = (GatewayInfo("Ethernet", "192.168.1.1"),),
    arp_entries: tuple[ArpEntry, ...] = (),
) -> NetworkData:
    return NetworkData(
        hostname=hostname,
        ip_addresses=ips,
        gateways=gateways,
        arp_entries=arp_entries,
    )


def _printers(*printers: PrinterInfo) -> PrintersData:
    return PrintersData(printers=printers)


def test_pc_node_always_present():
    nodes = build_nodes(NetworkData(), PrintersData())

    pc = nodes[0]
    assert pc["id"] == "pc"
    assert pc["label"] == "This PC"
    assert pc["node_type"] == "pc"


def test_gateway_node_when_gateways_exist():
    nodes = build_nodes(_network(), PrintersData())

    gateway = next(node for node in nodes if node["node_type"] == "gateway")
    assert gateway["id"] == "gw"
    assert gateway["label"] == "Gateway"
    assert gateway["sublabel"] == "192.168.1.1"


def test_no_gateway_node_when_no_gateways():
    nodes = build_nodes(_network(gateways=()), PrintersData())

    assert not any(node["node_type"] == "gateway" for node in nodes)


def test_arp_entries_become_device_nodes():
    arp = (ArpEntry("Ethernet", "192.168.1.55", "AA-BB-CC", "Reachable"),)

    nodes = build_nodes(_network(arp_entries=arp), PrintersData())

    device = next(node for node in nodes if node["node_type"] == "device")
    assert device["id"] == "arp_192.168.1.55"
    assert device["label"] == "192.168.1.55"
    assert device["sublabel"] == "AA-BB-CC"


def test_gateway_ip_excluded_from_devices():
    arp = (
        ArpEntry("Ethernet", "192.168.1.1", "GW-MAC", "Reachable"),
        ArpEntry("Ethernet", "192.168.1.10", "PC-MAC", "Reachable"),
        ArpEntry("Ethernet", "192.168.1.80", "DEVICE-MAC", "Reachable"),
    )

    nodes = build_nodes(_network(arp_entries=arp), PrintersData())
    device_labels = [node["label"] for node in nodes if node["node_type"] == "device"]

    assert device_labels == ["192.168.1.80"]


def test_printers_only_network_or_default():
    printers = _printers(
        PrinterInfo("Local ignored", printer_type="Local"),
        PrinterInfo("Network shown", printer_type="Connection"),
        PrinterInfo("Default local", printer_type="Local", is_default=True),
    )

    nodes = build_nodes(_network(), printers)
    printer_labels = [node["label"] for node in nodes if node["node_type"] == "printer"]

    assert printer_labels == ["Network shown", "Default local"]


def test_printer_label_truncated_at_14_chars():
    printers = _printers(PrinterInfo("Very Long Printer Name", printer_type="Connection"))

    nodes = build_nodes(_network(), printers)
    printer = next(node for node in nodes if node["node_type"] == "printer")

    assert printer["label"] == "Very Long Prin"
    assert len(printer["label"]) == 14


def test_pc_at_correct_x():
    nodes = build_nodes(_network(), PrintersData())

    positions = compute_positions(nodes, 800, 600)

    assert positions["pc"][0] == 110
    assert positions["pc"][1] == 300


def test_gateway_at_correct_x():
    nodes = build_nodes(_network(), PrintersData())

    positions = compute_positions(nodes, 800, 600)

    assert positions["gw"][0] == 330  # 110 + _COL_W(220)
    assert positions["gw"][1] == 300


def test_devices_evenly_spaced_y():
    arp = (
        ArpEntry("Ethernet", "192.168.1.20", "MAC-20", "Reachable"),
        ArpEntry("Ethernet", "192.168.1.30", "MAC-30", "Reachable"),
        ArpEntry("Ethernet", "192.168.1.40", "MAC-40", "Reachable"),
    )
    nodes = build_nodes(_network(arp_entries=arp), PrintersData())

    positions = compute_positions(nodes, 800, 600)
    y_values = [positions[f"arp_192.168.1.{last}"][1] for last in (20, 30, 40)]

    # 3 devices, _NODE_V_GAP=88, centered around canvas_h/2=300:
    # start_y = 300 - 88 = 212; values = [212, 300, 388]
    assert y_values[1] == 300  # middle device always at center
    gap = y_values[1] - y_values[0]
    assert gap == y_values[2] - y_values[1]  # equal spacing
    assert gap == 88
