from unittest.mock import MagicMock

import pytest

from app.core.command_result import CommandResult
from app.modules.network.models import NetworkData
from app.modules.network.scanner import NetworkScanner, _as_list, _format_speed

# --------------------------------------------------------------------------- helpers


def _run_ok(stdout: str = "") -> CommandResult:
    return CommandResult(command="cmd", stdout=stdout, exit_code=0)


def _run_fail(stderr: str = "err") -> CommandResult:
    return CommandResult(command="cmd", exit_code=1, stderr=stderr)


def _json_ok(data: object) -> CommandResult:
    return CommandResult(command="cmd", stdout="...", exit_code=0, parsed_json=data)


def _json_fail() -> CommandResult:
    return CommandResult(command="cmd", exit_code=1)


def _make_scanner(run_return=None, run_json_side=None) -> NetworkScanner:
    runner = MagicMock()
    runner.run.return_value = run_return or _run_ok("TESTPC")
    if run_json_side is not None:
        runner.run_json.side_effect = run_json_side
    else:
        runner.run_json.return_value = _json_fail()
    return NetworkScanner(runner)


def _all_null_side(n: int, overrides: dict[int, object] | None = None) -> list:
    """n run_json calls all returning empty; overrides[i] replaces call i."""
    overrides = overrides or {}
    return [overrides.get(i, _json_fail()) for i in range(n)]


# --------------------------------------------------------------------------- helpers unit tests


class TestAsListHelper:
    def test_none_returns_empty(self):
        assert _as_list(None) == []

    def test_dict_wrapped_in_list(self):
        d = {"a": 1}
        assert _as_list(d) == [d]

    def test_list_returned_unchanged(self):
        lst = [{"a": 1}, {"b": 2}]
        assert _as_list(lst) is lst

    def test_unexpected_scalar_returns_empty(self):
        # Scalars don't come from PS JSON for these cmdlets — safely ignored
        assert _as_list(42) == []


class TestFormatSpeed:
    def test_gbps(self):
        assert _format_speed(1_000_000_000) == "1 Gbps"

    def test_mbps(self):
        assert _format_speed(100_000_000) == "100 Mbps"

    def test_kbps(self):
        assert _format_speed(512_000) == "512 Kbps"

    def test_bps(self):
        assert _format_speed(500) == "500 bps"

    def test_none_returns_none(self):
        assert _format_speed(None) is None


# --------------------------------------------------------------------------- scanner tests


class TestScanReturnsNetworkData:
    def test_returns_networkdata_instance(self):
        scanner = _make_scanner()
        assert isinstance(scanner.scan(), NetworkData)

    def test_duration_ms_non_negative(self):
        scanner = _make_scanner()
        assert scanner.scan().scan_duration_ms >= 0


class TestHostname:
    def test_hostname_populated(self):
        scanner = _make_scanner(run_return=_run_ok("MYPC"))
        data = scanner.scan()
        assert data.hostname == "MYPC"

    def test_hostname_empty_on_failure(self):
        scanner = _make_scanner(run_return=_run_fail())
        data = scanner.scan()
        assert data.hostname == ""

    def test_hostname_failure_adds_error(self):
        scanner = _make_scanner(run_return=_run_fail("Access denied"))
        data = scanner.scan()
        assert any("hostname" in e for e in data.errors)


class TestAdapters:
    # run_json call order: adapters(0), ip(1), gateways(2), dns(3), profiles(4), arp(5)
    _ADAPTER = {
        "Name": "Ethernet",
        "InterfaceDescription": "Intel NIC",
        "Status": "Up",
        "Speed": 1_000_000_000,
        "MacAddress": "AA-BB-CC-DD-EE-FF",
    }

    def test_single_adapter_as_dict(self):
        scanner = _make_scanner(
            run_json_side=_all_null_side(6, {0: _json_ok(self._ADAPTER)})
        )
        data = scanner.scan()
        assert len(data.adapters) == 1
        assert data.adapters[0].name == "Ethernet"
        assert data.adapters[0].link_speed_bps == 1_000_000_000

    def test_multiple_adapters_as_list(self):
        two = [self._ADAPTER, {**self._ADAPTER, "Name": "WiFi"}]
        scanner = _make_scanner(run_json_side=_all_null_side(6, {0: _json_ok(two)}))
        data = scanner.scan()
        assert len(data.adapters) == 2
        assert data.adapters[1].name == "WiFi"

    def test_failed_adapter_query_appends_error(self):
        scanner = _make_scanner(run_json_side=_all_null_side(6))
        data = scanner.scan()
        assert any("Get-NetAdapter" in e for e in data.errors)


class TestIPAddresses:
    _IP = {"InterfaceAlias": "Ethernet", "IPAddress": "192.168.1.10", "PrefixLength": 24}

    def test_ip_parsed(self):
        scanner = _make_scanner(run_json_side=_all_null_side(6, {1: _json_ok(self._IP)}))
        data = scanner.scan()
        assert len(data.ip_addresses) == 1
        assert data.ip_addresses[0].ip_address == "192.168.1.10"
        assert data.ip_addresses[0].prefix_length == 24


class TestGateways:
    _GW = {"InterfaceAlias": "Ethernet", "NextHop": "192.168.1.1", "RouteMetric": 0}

    def test_gateway_parsed(self):
        # With a gateway found, ping is also called → 7 run_json calls total
        scanner = _make_scanner(
            run_json_side=_all_null_side(7, {2: _json_ok(self._GW), 5: _json_ok(True)})
        )
        data = scanner.scan()
        assert len(data.gateways) == 1
        assert data.gateways[0].next_hop == "192.168.1.1"


class TestDNS:
    _DNS = {"InterfaceAlias": "Ethernet", "ServerAddresses": ["8.8.8.8", "8.8.4.4"]}

    def test_dns_servers_parsed(self):
        scanner = _make_scanner(run_json_side=_all_null_side(6, {3: _json_ok(self._DNS)}))
        data = scanner.scan()
        assert len(data.dns) == 1
        assert data.dns[0].servers == ("8.8.8.8", "8.8.4.4")

    def test_single_server_string_normalized(self):
        single = {"InterfaceAlias": "Ethernet", "ServerAddresses": "1.1.1.1"}
        scanner = _make_scanner(run_json_side=_all_null_side(6, {3: _json_ok(single)}))
        data = scanner.scan()
        assert data.dns[0].servers == ("1.1.1.1",)


class TestNetworkProfiles:
    def test_private_profile(self):
        profile = {"Name": "Home", "InterfaceAlias": "Ethernet", "NetworkCategory": 1}
        scanner = _make_scanner(run_json_side=_all_null_side(6, {4: _json_ok(profile)}))
        data = scanner.scan()
        assert len(data.profiles) == 1
        assert data.profiles[0].category == "Private"

    def test_public_profile(self):
        profile = {"Name": "Net", "InterfaceAlias": "WiFi", "NetworkCategory": 0}
        scanner = _make_scanner(run_json_side=_all_null_side(6, {4: _json_ok(profile)}))
        data = scanner.scan()
        assert data.profiles[0].category == "Public"

    def test_unknown_category_int(self):
        profile = {"Name": "Net", "InterfaceAlias": "WiFi", "NetworkCategory": 99}
        scanner = _make_scanner(run_json_side=_all_null_side(6, {4: _json_ok(profile)}))
        data = scanner.scan()
        assert "Unknown" in data.profiles[0].category


class TestPingGateway:
    _GW = {"InterfaceAlias": "Ethernet", "NextHop": "192.168.1.1", "RouteMetric": 0}

    def test_ping_true(self):
        # gateways at index 2, ping at index 5 (after gateways found → 7 total)
        scanner = _make_scanner(
            run_json_side=_all_null_side(7, {2: _json_ok(self._GW), 5: _json_ok(True)})
        )
        assert scanner.scan().gateway_reachable is True

    def test_ping_false(self):
        scanner = _make_scanner(
            run_json_side=_all_null_side(7, {2: _json_ok(self._GW), 5: _json_ok(False)})
        )
        assert scanner.scan().gateway_reachable is False

    def test_no_gateways_returns_none(self):
        scanner = _make_scanner(run_json_side=_all_null_side(6))
        assert scanner.scan().gateway_reachable is None

    def test_gateway_all_zeros_skips_ping(self):
        gw = {"InterfaceAlias": "Loopback", "NextHop": "0.0.0.0", "RouteMetric": 0}
        scanner = _make_scanner(run_json_side=_all_null_side(6, {2: _json_ok(gw)}))
        assert scanner.scan().gateway_reachable is None


class TestArpEntries:
    _ARP = {
        "InterfaceAlias": "Ethernet",
        "IPAddress": "192.168.1.1",
        "LinkLayerAddress": "AA-BB-CC-DD-EE-FF",
        "State": "Reachable",
    }

    def test_arp_entry_parsed(self):
        scanner = _make_scanner(run_json_side=_all_null_side(6, {5: _json_ok(self._ARP)}))
        data = scanner.scan()
        assert len(data.arp_entries) == 1
        assert data.arp_entries[0].ip_address == "192.168.1.1"
        assert data.arp_entries[0].state == "Reachable"

    def test_failed_arp_adds_error(self):
        scanner = _make_scanner(run_json_side=_all_null_side(6))
        data = scanner.scan()
        assert any("Get-NetNeighbor" in e for e in data.errors)


class TestErrorCollection:
    def test_multiple_failures_all_collected(self):
        scanner = _make_scanner(
            run_return=_run_fail(),
            run_json_side=_all_null_side(6),
        )
        data = scanner.scan()
        # hostname + all 6 run_json calls (adapters, ip, gateways, dns, profiles, arp)
        assert len(data.errors) >= 6
