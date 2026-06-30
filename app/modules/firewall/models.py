from dataclasses import dataclass


@dataclass(frozen=True)
class FirewallProfile:
    name: str
    enabled: bool | None = None
    default_inbound: str = ""
    default_outbound: str = ""


@dataclass(frozen=True)
class FirewallRule:
    name: str
    display_name: str = ""
    direction: str = ""
    action: str = ""
    enabled: bool | None = None
    profile: str = ""


@dataclass(frozen=True)
class FirewallData:
    profiles: tuple[FirewallProfile, ...] = ()
    file_sharing_rules: tuple[FirewallRule, ...] = ()
    network_discovery_rules: tuple[FirewallRule, ...] = ()
    scan_duration_ms: float = 0.0
    errors: tuple[str, ...] = ()
