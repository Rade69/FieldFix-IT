from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceInfo:
    name: str
    display_name: str = ""
    status: str = ""       # "Running", "Stopped", "StartPending", etc.
    start_type: str = ""   # "Automatic", "Manual", "Disabled", etc.
    required_for: str = "" # human-readable context shown in GUI


@dataclass(frozen=True)
class ServicesData:
    """Snapshot of monitored Windows service states. All fields read-only."""

    services: tuple[ServiceInfo, ...] = ()
    scan_duration_ms: float = 0.0
    errors: tuple[str, ...] = ()
