import time

from app.core.powershell_runner import PowerShellRunner
from app.modules.services.models import ServiceInfo, ServicesData

# Services monitored by FieldFix IT — all relevant to networking, sharing, printing.
MONITORED_SERVICES: dict[str, str] = {
    "LanmanServer":     "File and Printer Sharing (dijeljenje resursa sa mrežom)",
    "LanmanWorkstation": "Pristup mrežnim shareovima (Workstation servis)",
    "FDResPub":         "Network Discovery — objava ovog računara na mreži",
    "fdPHost":          "Network Discovery — pronalaženje uređaja na mreži",
    "Dnscache":         "DNS Client — keširanje DNS rezolucije",
    "SSDPSRV":          "SSDP Discovery — UPnP i Network Discovery",
    "upnphost":         "UPnP Device Host — dijeljenje UPnP resursa",
    "Spooler":          "Print Spooler — upravljanje štampom",
}

# PS ServiceControllerStatus enum integers → string (fallback kad PS vrati int)
_STATUS_MAP: dict[int, str] = {
    1: "Stopped",
    2: "StartPending",
    3: "StopPending",
    4: "Running",
    5: "ContinuePending",
    6: "PausePending",
    7: "Paused",
}

# PS ServiceStartMode enum integers → string
_START_TYPE_MAP: dict[int, str] = {
    0: "Boot",
    1: "System",
    2: "Automatic",
    3: "Manual",
    4: "Disabled",
}

_SERVICE_NAMES = ", ".join(MONITORED_SERVICES.keys())


def _normalize(value: object, mapping: dict[int, str]) -> str:
    """Convert PS enum integer or string to normalized string."""
    if isinstance(value, int):
        return mapping.get(value, str(value))
    return str(value) if value is not None else ""


class ServicesScanner:
    """Checks status of Windows services relevant to networking and printing. Read-only."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def scan(self) -> ServicesData:
        start = time.monotonic()
        errors: list[str] = []
        services = self._get_services(errors)
        return ServicesData(
            services=tuple(services),
            scan_duration_ms=(time.monotonic() - start) * 1000,
            errors=tuple(errors),
        )

    def _get_services(self, errors: list[str]) -> list[ServiceInfo]:
        # Force string serialization of Status and StartType to avoid int enum ambiguity
        cmd = (
            f"Get-Service -Name {_SERVICE_NAMES} -ErrorAction SilentlyContinue | "
            "Select-Object Name, DisplayName, "
            "@{N='Status';E={$_.Status.ToString()}}, "
            "@{N='StartType';E={$_.StartType.ToString()}} | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=20)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-Service: {result.stderr or 'no output'}")
            return []

        raw = result.parsed_json
        if isinstance(raw, dict):
            raw = [raw]

        services: list[ServiceInfo] = []
        found_names = set()
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("Name", ""))
            found_names.add(name)
            services.append(ServiceInfo(
                name=name,
                display_name=str(item.get("DisplayName", "")),
                status=_normalize(item.get("Status"), _STATUS_MAP),
                start_type=_normalize(item.get("StartType"), _START_TYPE_MAP),
                required_for=MONITORED_SERVICES.get(name, ""),
            ))

        # Services missing from PS output are likely not installed — report them
        for name in MONITORED_SERVICES:
            if name not in found_names:
                errors.append(f"Servis '{name}' nije pronađen na sistemu.")
                services.append(ServiceInfo(
                    name=name,
                    status="NotFound",
                    required_for=MONITORED_SERVICES[name],
                ))

        # Preserve defined order (MONITORED_SERVICES order)
        order = list(MONITORED_SERVICES.keys())
        services.sort(key=lambda s: order.index(s.name) if s.name in order else 999)
        return services
