import time

from app.core.powershell_runner import PowerShellRunner
from app.modules.printers.models import PrinterInfo, PrintJob, PrintersData


class PrintersScanner:
    """Collects installed printer and print-job data via PowerShell. Read-only."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def scan(self) -> PrintersData:
        start = time.monotonic()
        errors: list[str] = []

        default_name = self._get_default_printer_name(errors)
        printers = self._get_printers(errors, default_name)
        jobs = self._get_print_jobs(errors)

        return PrintersData(
            printers=tuple(printers),
            print_jobs=tuple(jobs),
            scan_duration_ms=(time.monotonic() - start) * 1000,
            errors=tuple(errors),
        )

    # ------------------------------------------------------------------ private

    def _get_default_printer_name(self, errors: list[str]) -> str:
        cmd = (
            "Get-CimInstance -ClassName Win32_Printer "
            "-Filter \"Default='True'\" -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 Name | ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if result.succeeded and isinstance(result.parsed_json, dict):
            return str(result.parsed_json.get("Name", "") or "")
        # Non-fatal — default printer may not be set
        return ""

    def _get_printers(self, errors: list[str], default_name: str) -> list[PrinterInfo]:
        # ToString() forces string output for PS enum properties (Type, PrinterStatus)
        cmd = (
            "Get-Printer -ErrorAction SilentlyContinue | "
            "Select-Object Name, DriverName, PortName, "
            "@{N='PrinterType';E={$_.Type.ToString()}}, "
            "Shared, ShareName, "
            "@{N='PrinterStatus';E={$_.PrinterStatus.ToString()}}, "
            "JobCount | ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=20)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-Printer: {result.stderr or 'no output'}")
            return []

        raw = result.parsed_json
        if isinstance(raw, dict):
            raw = [raw]

        printers: list[PrinterInfo] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("Name", ""))
            shared = item.get("Shared")
            printers.append(PrinterInfo(
                name=name,
                driver_name=str(item.get("DriverName", "") or ""),
                port_name=str(item.get("PortName", "") or ""),
                printer_type=str(item.get("PrinterType", "") or ""),
                shared=bool(shared) if isinstance(shared, bool) else None,
                share_name=str(item.get("ShareName", "") or ""),
                status=str(item.get("PrinterStatus", "") or ""),
                job_count=int(item.get("JobCount") or 0),
                is_default=(name == default_name) if default_name else False,
            ))
        return printers

    def _get_print_jobs(self, errors: list[str]) -> list[PrintJob]:
        cmd = (
            "Get-Printer -ErrorAction SilentlyContinue | "
            "Get-PrintJob -ErrorAction SilentlyContinue | "
            "Select-Object Id, PrinterName, DocumentName, UserName, TotalPages, "
            "@{N='JobStatus';E={$_.JobStatus.ToString()}} | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=20)
        if not result.succeeded or result.parsed_json is None:
            # No jobs is normal — don't add to errors unless there was a real failure
            if result.stderr:
                errors.append(f"Get-PrintJob: {result.stderr}")
            return []

        raw = result.parsed_json
        if isinstance(raw, dict):
            raw = [raw]

        jobs: list[PrintJob] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            pages = item.get("TotalPages")
            jobs.append(PrintJob(
                job_id=int(item.get("Id") or 0),
                printer_name=str(item.get("PrinterName", "") or ""),
                document_name=str(item.get("DocumentName", "") or ""),
                user_name=str(item.get("UserName", "") or ""),
                total_pages=int(pages) if isinstance(pages, (int, float)) else None,
                status=str(item.get("JobStatus", "") or ""),
            ))
        return jobs
