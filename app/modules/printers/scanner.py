import re
import socket
import time

from app.core.powershell_runner import PowerShellRunner
from app.modules.printers.models import PrinterInfo, PrintJob, PrintersData

_IP_RE = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def _resolve_wsd_hostname(display_name: str) -> str:
    """Try to resolve a WSD printer's display name to an IPv4 address.

    Windows registers WSD device hostnames in its local DNS/mDNS resolver,
    so the first word of the printer name (e.g. 'CANONABC123', 'EPSONDF0F56')
    is usually resolvable directly via getaddrinfo().
    """
    hostname = display_name.split("(")[0].strip().split()[0] if display_name else ""
    if not hostname:
        return ""
    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None, socket.AF_INET):
            return sockaddr[0]
    except OSError:
        return ""
    return ""


class PrintersScanner:
    """Collects installed printer and print-job data via PowerShell. Read-only."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def scan(self) -> PrintersData:
        start = time.monotonic()
        errors: list[str] = []

        default_name = self._get_default_printer_name(errors)
        port_ip_map = self._resolve_printer_ips(errors)
        printers = self._get_printers(errors, default_name, port_ip_map)
        jobs = self._get_print_jobs(errors)

        return PrintersData(
            printers=tuple(printers),
            print_jobs=tuple(jobs),
            scan_duration_ms=(time.monotonic() - start) * 1000,
            errors=tuple(errors),
        )

    # ------------------------------------------------------------------ private

    def _resolve_printer_ips(self, errors: list[str]) -> dict[str, str]:
        """Return {port_name: ip_address} for all resolvable printer ports.

        Covers:
        - Win32_TCPIPPrinterPort (standard IP ports, e.g. IP_192.168.x.x)
        - MSFT_PrinterPort in root/PrintManagement (WSD and others)
        - IP embedded in the port name itself as a last resort
        """
        cmd = (
            "$out = @{};"
            # Standard TCP/IP ports
            "Get-CimInstance Win32_TCPIPPrinterPort -ErrorAction SilentlyContinue | "
            "ForEach-Object { if ($_.HostAddress) { $out[$_.Name] = $_.HostAddress } };"
            # WSD and other ports via root/PrintManagement
            "Get-CimInstance -Namespace root\\PrintManagement -ClassName MSFT_PrinterPort "
            "-ErrorAction SilentlyContinue | ForEach-Object {"
            "  $n = $_.Name; if ($out.ContainsKey($n)) { return };"
            "  $ha = $_.HostAddress;"
            "  if ($ha -match '(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})') { $out[$n] = $Matches[1]; return };"
            "  $du = $_.DeviceUrl;"
            "  if ($du -match '(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})') { $out[$n] = $Matches[1] }"
            "};"
            "$out | ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if result.succeeded and isinstance(result.parsed_json, dict):
            return {k: str(v) for k, v in result.parsed_json.items() if v}
        return {}

    def _get_default_printer_name(self, errors: list[str]) -> str:
        cmd = (
            "Get-CimInstance -ClassName Win32_Printer "
            "-Filter \"Default='True'\" -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 Name | ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if result.succeeded and isinstance(result.parsed_json, dict):
            return str(result.parsed_json.get("Name", "") or "")
        return ""

    def _get_printers(
        self,
        errors: list[str],
        default_name: str,
        port_ip_map: dict[str, str],
    ) -> list[PrinterInfo]:
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
            port_name = str(item.get("PortName", "") or "")
            shared = item.get("Shared")

            # Resolve IP: port_ip_map → regex in port name → WSD hostname resolution
            ip = port_ip_map.get(port_name, "")
            if not ip:
                m = _IP_RE.search(port_name)
                ip = m.group(0) if m else ""
            if not ip and port_name.startswith("WSD-"):
                ip = _resolve_wsd_hostname(name)

            printers.append(PrinterInfo(
                name=name,
                driver_name=str(item.get("DriverName", "") or ""),
                port_name=port_name,
                printer_type=str(item.get("PrinterType", "") or ""),
                shared=bool(shared) if isinstance(shared, bool) else None,
                share_name=str(item.get("ShareName", "") or ""),
                status=str(item.get("PrinterStatus", "") or ""),
                job_count=int(item.get("JobCount") or 0),
                is_default=(name == default_name) if default_name else False,
                ip_address=ip,
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
