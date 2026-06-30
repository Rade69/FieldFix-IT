from dataclasses import dataclass


@dataclass(frozen=True)
class PrinterInfo:
    name: str
    driver_name: str = ""
    port_name: str = ""
    printer_type: str = ""    # "Local", "Connection"
    shared: bool | None = None
    share_name: str = ""
    status: str = ""          # "Normal", "Error", "Offline", "Paused", etc.
    job_count: int = 0
    is_default: bool = False


@dataclass(frozen=True)
class PrintJob:
    job_id: int
    printer_name: str = ""
    document_name: str = ""
    user_name: str = ""
    total_pages: int | None = None
    status: str = ""          # "Normal", "Error", "Deleting", flags combination, etc.


@dataclass(frozen=True)
class PrintersData:
    """Snapshot of installed printers and active print jobs. All fields read-only."""

    printers: tuple[PrinterInfo, ...] = ()
    print_jobs: tuple[PrintJob, ...] = ()
    scan_duration_ms: float = 0.0
    errors: tuple[str, ...] = ()
