from dataclasses import dataclass

from app.modules.network.models import NetworkData
from app.modules.printers.models import PrintersData
from app.modules.services.models import ServicesData
from app.modules.smb.models import SmbData


@dataclass(frozen=True)
class ScanReport:
    """Aggregated result of one or more module scans, ready for export.

    Sections that were not scanned carry None — report writers emit a
    "Not scanned" notice for those sections rather than skipping them.
    """

    generated_at: str           # ISO 8601, e.g. "2026-06-30T15:30:00"
    hostname: str = ""
    network: NetworkData | None = None
    smb: SmbData | None = None
    smb_target_ip: str = ""     # IP used for SMB port/net-view scan (may be empty)
    services: ServicesData | None = None
    printers: PrintersData | None = None
