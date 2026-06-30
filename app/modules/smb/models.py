from dataclasses import dataclass


@dataclass(frozen=True)
class SmbServerConfig:
    smb1_enabled: bool | None = None
    smb2_enabled: bool | None = None
    require_security_signature: bool | None = None
    enable_security_signature: bool | None = None
    enable_insecure_guest_logons_server: bool | None = None


@dataclass(frozen=True)
class SmbClientConfig:
    smb1_enabled: bool | None = None
    require_security_signature: bool | None = None
    enable_security_signature: bool | None = None
    enable_insecure_guest_logons: bool | None = None


@dataclass(frozen=True)
class SmbShare:
    name: str
    path: str = ""
    description: str = ""
    share_type: str = ""


@dataclass(frozen=True)
class PortCheckResult:
    target_ip: str
    port: int = 445
    reachable: bool | None = None
    error: str = ""


@dataclass(frozen=True)
class NetViewEntry:
    name: str
    share_type: str = ""
    comment: str = ""


@dataclass(frozen=True)
class SmbData:
    """Snapshot of SMB state collected by SmbScanner. All fields read-only."""

    server_config: SmbServerConfig | None = None
    client_config: SmbClientConfig | None = None
    shares: tuple[SmbShare, ...] = ()
    port_445: PortCheckResult | None = None
    net_view_success: bool | None = None
    net_view_entries: tuple[NetViewEntry, ...] = ()
    net_view_error_code: int | None = None
    scan_duration_ms: float = 0.0
    errors: tuple[str, ...] = ()
