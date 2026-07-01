from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterInfo:
    name: str
    description: str = ""
    status: str = ""
    link_speed_bps: int | None = None
    mac_address: str | None = None


@dataclass(frozen=True)
class IPAddressInfo:
    interface_alias: str
    ip_address: str
    prefix_length: int | None = None


@dataclass(frozen=True)
class GatewayInfo:
    interface_alias: str
    next_hop: str
    metric: int | None = None


@dataclass(frozen=True)
class DNSInfo:
    interface_alias: str
    servers: tuple[str, ...]


@dataclass(frozen=True)
class NetworkProfile:
    name: str
    interface_alias: str
    category: str  # "Public", "Private", "DomainAuthenticated", "Unknown(N)"


@dataclass(frozen=True)
class ArpEntry:
    interface_alias: str
    ip_address: str
    mac_address: str
    state: str


@dataclass(frozen=True)
class OsFingerprint:
    name: str
    confidence: str = "LOW"
    detected_by: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveredDevice:
    """One host found by active subnet scan."""
    ip_address: str
    mac_address: str = ""
    hostname: str = ""
    device_type: str = "unknown"  # pc | printer | router | web_device | unknown
    open_ports: tuple[int, ...] = ()
    confidence: str = "LOW"
    detected_by: str = "ping"


@dataclass(frozen=True)
class NetworkData:
    """Snapshot of network state collected by NetworkScanner. All fields read-only."""

    hostname: str = ""
    local_os: OsFingerprint | None = None
    adapters: tuple[AdapterInfo, ...] = ()
    ip_addresses: tuple[IPAddressInfo, ...] = ()
    gateways: tuple[GatewayInfo, ...] = ()
    dns: tuple[DNSInfo, ...] = ()
    profiles: tuple[NetworkProfile, ...] = ()
    gateway_reachable: bool | None = None
    arp_entries: tuple[ArpEntry, ...] = ()
    scan_duration_ms: float = 0.0
    errors: tuple[str, ...] = ()
