import time

from app.core.powershell_runner import PowerShellRunner
from app.modules.network.models import (
    AdapterInfo,
    ArpEntry,
    DNSInfo,
    GatewayInfo,
    IPAddressInfo,
    NetworkData,
    NetworkProfile,
    OsFingerprint,
)

_NETWORK_CATEGORY = {0: "Public", 1: "Private", 3: "DomainAuthenticated"}


def _as_list(data: object) -> list:
    """Normalize PS JSON output: single object → list, None → [], list → list."""
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def _parse_speed(raw: object) -> int | None:
    """Convert PS Speed value to int bps. PS may return UInt64 as string."""
    if raw is None:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def _format_speed(bps: object) -> str | None:
    if bps is None:
        return None
    try:
        bps = int(bps)  # PS may serialize UInt64 as string depending on version
    except (ValueError, TypeError):
        return str(bps) or None
    if bps >= 1_000_000_000:
        return f"{bps // 1_000_000_000} Gbps"
    if bps >= 1_000_000:
        return f"{bps // 1_000_000} Mbps"
    if bps >= 1_000:
        return f"{bps // 1_000} Kbps"
    return f"{bps} bps"


class NetworkScanner:
    """Collects network diagnostics via PowerShell. Read-only — no Windows settings changed."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def scan(self) -> NetworkData:
        """Run all network checks and return a NetworkData snapshot."""
        start = time.monotonic()
        errors: list[str] = []

        hostname = self._get_hostname(errors)
        adapters = self._get_adapters(errors)
        ip_addresses = self._get_ip_addresses(errors)
        gateways = self._get_gateways(errors)
        dns = self._get_dns(errors)
        profiles = self._get_profiles(errors)
        gateway_reachable = self._ping_gateway(gateways, errors)
        arp_entries = self._get_arp_entries(errors)
        local_os = self._get_local_os(errors)

        return NetworkData(
            hostname=hostname,
            local_os=local_os,
            adapters=tuple(adapters),
            ip_addresses=tuple(ip_addresses),
            gateways=tuple(gateways),
            dns=tuple(dns),
            profiles=tuple(profiles),
            gateway_reachable=gateway_reachable,
            arp_entries=tuple(arp_entries),
            scan_duration_ms=(time.monotonic() - start) * 1000,
            errors=tuple(errors),
        )

    def _get_hostname(self, errors: list[str]) -> str:
        result = self._runner.run("[System.Net.Dns]::GetHostName()", timeout=10)
        if result.succeeded:
            return result.stdout
        errors.append(f"hostname: {result.stderr or 'failed'}")
        return ""

    def _get_local_os(self, errors: list[str]) -> OsFingerprint | None:
        cmd = (
            "Get-CimInstance Win32_OperatingSystem | "
            "Select-Object Caption, Version, BuildNumber | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or not isinstance(result.parsed_json, dict):
            errors.append(f"Win32_OperatingSystem: {result.stderr or 'no output'}")
            return None

        caption = str(result.parsed_json.get("Caption", "")).strip()
        version = str(result.parsed_json.get("Version", "")).strip()
        build = str(result.parsed_json.get("BuildNumber", "")).strip()
        name = caption or "Windows"
        if version and build:
            name = f"{name} ({version}, build {build})"
        elif version:
            name = f"{name} ({version})"
        elif build:
            name = f"{name} (build {build})"

        return OsFingerprint(
            name=name,
            confidence="HIGH",
            detected_by=("local Windows OS query",),
        )

    def _get_adapters(self, errors: list[str]) -> list[AdapterInfo]:
        cmd = (
            "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
            "Select-Object Name, InterfaceDescription, Status, Speed, MacAddress | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-NetAdapter: {result.stderr or 'no output'}")
            return []
        return [
            AdapterInfo(
                name=str(item.get("Name", "")),
                description=str(item.get("InterfaceDescription", "")),
                status=str(item.get("Status", "")),
                link_speed_bps=_parse_speed(item.get("Speed")),
                mac_address=item.get("MacAddress"),
            )
            for item in _as_list(result.parsed_json)
        ]

    def _get_ip_addresses(self, errors: list[str]) -> list[IPAddressInfo]:
        cmd = (
            "Get-NetIPAddress | "
            "Where-Object {$_.AddressFamily -eq 'IPv4' -and $_.PrefixOrigin -ne 'WellKnown'} | "
            "Select-Object InterfaceAlias, IPAddress, PrefixLength | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-NetIPAddress: {result.stderr or 'no output'}")
            return []
        return [
            IPAddressInfo(
                interface_alias=str(item.get("InterfaceAlias", "")),
                ip_address=str(item.get("IPAddress", "")),
                prefix_length=item.get("PrefixLength"),
            )
            for item in _as_list(result.parsed_json)
        ]

    def _get_gateways(self, errors: list[str]) -> list[GatewayInfo]:
        cmd = (
            "Get-NetRoute | Where-Object {$_.DestinationPrefix -eq '0.0.0.0/0'} | "
            "Select-Object InterfaceAlias, NextHop, RouteMetric | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-NetRoute: {result.stderr or 'no output'}")
            return []
        return [
            GatewayInfo(
                interface_alias=str(item.get("InterfaceAlias", "")),
                next_hop=str(item.get("NextHop", "")),
                metric=item.get("RouteMetric"),
            )
            for item in _as_list(result.parsed_json)
        ]

    def _get_dns(self, errors: list[str]) -> list[DNSInfo]:
        cmd = (
            "Get-DnsClientServerAddress | "
            "Where-Object {$_.AddressFamily -eq 2 -and $_.ServerAddresses.Count -gt 0} | "
            "Select-Object InterfaceAlias, ServerAddresses | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-DnsClientServerAddress: {result.stderr or 'no output'}")
            return []
        dns_list = []
        for item in _as_list(result.parsed_json):
            raw_servers = item.get("ServerAddresses", [])
            if isinstance(raw_servers, str):
                raw_servers = [raw_servers]
            dns_list.append(DNSInfo(
                interface_alias=str(item.get("InterfaceAlias", "")),
                servers=tuple(str(s) for s in raw_servers),
            ))
        return dns_list

    def _get_profiles(self, errors: list[str]) -> list[NetworkProfile]:
        cmd = (
            "Get-NetConnectionProfile | "
            "Select-Object Name, InterfaceAlias, NetworkCategory | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-NetConnectionProfile: {result.stderr or 'no output'}")
            return []
        profiles = []
        for item in _as_list(result.parsed_json):
            category_int = item.get("NetworkCategory", -1)
            category = _NETWORK_CATEGORY.get(category_int, f"Unknown({category_int})")
            profiles.append(NetworkProfile(
                name=str(item.get("Name", "")),
                interface_alias=str(item.get("InterfaceAlias", "")),
                category=category,
            ))
        return profiles

    def _ping_gateway(self, gateways: list[GatewayInfo], errors: list[str]) -> bool | None:
        if not gateways:
            return None
        gw_ip = gateways[0].next_hop
        if not gw_ip or gw_ip == "0.0.0.0":
            return None
        cmd = (
            f"(Test-Connection -ComputerName '{gw_ip}' -Count 1 "
            f"-Quiet -ErrorAction SilentlyContinue) | ConvertTo-Json"
        )
        result = self._runner.run_json(cmd, timeout=10)
        if result.succeeded and result.parsed_json is not None:
            return bool(result.parsed_json)
        return None

    def _get_arp_entries(self, errors: list[str]) -> list[ArpEntry]:
        cmd = (
            "Get-NetNeighbor | "
            "Where-Object {$_.State -ne 'Unreachable' -and $_.State -ne 'Incomplete'} | "
            "Select-Object InterfaceAlias, IPAddress, LinkLayerAddress, State | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-NetNeighbor: {result.stderr or 'no output'}")
            return []
        return [
            ArpEntry(
                interface_alias=str(item.get("InterfaceAlias", "")),
                ip_address=str(item.get("IPAddress", "")),
                mac_address=str(item.get("LinkLayerAddress", "")),
                state=str(item.get("State", "")),
            )
            for item in _as_list(result.parsed_json)
        ]
