from unittest.mock import MagicMock

from app.core.command_result import CommandResult
from app.modules.printers.models import PrintersData
from app.modules.printers.scanner import PrintersScanner


def _json_ok(data: object) -> CommandResult:
    return CommandResult(command="cmd", stdout="...", exit_code=0, parsed_json=data)


def _json_fail(stderr: str = "") -> CommandResult:
    return CommandResult(command="cmd", exit_code=1, stderr=stderr)


def _make_scanner(default=None, printers=None, jobs=None) -> PrintersScanner:
    """Build scanner with mocked run_json side_effect order: default, printers, jobs."""
    runner = MagicMock()
    runner.run_json.side_effect = [
        default if default is not None else _json_fail(),
        printers if printers is not None else _json_fail(),
        jobs if jobs is not None else _json_ok(None),
    ]
    return PrintersScanner(runner)


def _printer_item(name: str = "HP LaserJet", **kwargs) -> dict:
    base = {
        "Name": name,
        "DriverName": "HP LaserJet Driver",
        "PortName": "IP_192.168.1.10",
        "PrinterType": "Connection",
        "Shared": False,
        "ShareName": None,
        "PrinterStatus": "Normal",
        "JobCount": 0,
    }
    base.update(kwargs)
    return base


def _job_item(job_id: int = 1, printer: str = "HP LaserJet", **kwargs) -> dict:
    base = {
        "Id": job_id,
        "PrinterName": printer,
        "DocumentName": "Report.pdf",
        "UserName": "radovan",
        "TotalPages": 4,
        "JobStatus": "Normal",
    }
    base.update(kwargs)
    return base


# ── scan() returns correct type ────────────────────────────────────────────────

class TestScanReturnsData:
    def test_returns_printers_data(self):
        scanner = _make_scanner()
        assert isinstance(scanner.scan(), PrintersData)

    def test_duration_non_negative(self):
        scanner = _make_scanner()
        assert scanner.scan().scan_duration_ms >= 0

    def test_empty_when_all_fail(self):
        scanner = _make_scanner()
        data = scanner.scan()
        assert data.printers == ()
        assert data.print_jobs == ()


# ── Default printer detection ──────────────────────────────────────────────────

class TestDefaultPrinter:
    def test_default_marked_correctly(self):
        default_resp = _json_ok({"Name": "HP LaserJet"})
        printers_resp = _json_ok([
            _printer_item("HP LaserJet"),
            _printer_item("Canon PIXMA"),
        ])
        scanner = _make_scanner(default=default_resp, printers=printers_resp)
        data = scanner.scan()
        hp = next(p for p in data.printers if p.name == "HP LaserJet")
        canon = next(p for p in data.printers if p.name == "Canon PIXMA")
        assert hp.is_default is True
        assert canon.is_default is False

    def test_no_default_when_query_fails(self):
        printers_resp = _json_ok([_printer_item("HP LaserJet")])
        scanner = _make_scanner(default=_json_fail(), printers=printers_resp)
        data = scanner.scan()
        assert data.printers[0].is_default is False

    def test_default_query_fail_is_non_fatal(self):
        """Failure to find default printer must not abort the scan."""
        printers_resp = _json_ok([_printer_item("HP LaserJet")])
        scanner = _make_scanner(default=_json_fail(), printers=printers_resp)
        data = scanner.scan()
        assert len(data.printers) == 1


# ── Printer list ───────────────────────────────────────────────────────────────

class TestGetPrinters:
    def test_single_printer_as_dict(self):
        scanner = _make_scanner(printers=_json_ok(_printer_item()))
        data = scanner.scan()
        assert len(data.printers) == 1

    def test_multiple_printers_as_list(self):
        items = [_printer_item("HP"), _printer_item("Canon"), _printer_item("Epson")]
        scanner = _make_scanner(printers=_json_ok(items))
        data = scanner.scan()
        assert len(data.printers) == 3

    def test_printer_fields_mapped(self):
        item = _printer_item("HP LaserJet", DriverName="HP PCL6", PortName="LPT1",
                             PrinterType="Local", Shared=True, ShareName="HP_Share",
                             PrinterStatus="Normal", JobCount=2)
        scanner = _make_scanner(printers=_json_ok(item))
        data = scanner.scan()
        p = data.printers[0]
        assert p.name == "HP LaserJet"
        assert p.driver_name == "HP PCL6"
        assert p.port_name == "LPT1"
        assert p.printer_type == "Local"
        assert p.shared is True
        assert p.share_name == "HP_Share"
        assert p.status == "Normal"
        assert p.job_count == 2

    def test_error_status_preserved(self):
        item = _printer_item(PrinterStatus="Error")
        scanner = _make_scanner(printers=_json_ok(item))
        data = scanner.scan()
        assert data.printers[0].status == "Error"

    def test_offline_status_preserved(self):
        item = _printer_item(PrinterStatus="Offline")
        scanner = _make_scanner(printers=_json_ok(item))
        data = scanner.scan()
        assert data.printers[0].status == "Offline"

    def test_none_fields_become_empty_string(self):
        item = _printer_item(PortName=None, ShareName=None, DriverName=None)
        scanner = _make_scanner(printers=_json_ok(item))
        data = scanner.scan()
        p = data.printers[0]
        assert p.port_name == ""
        assert p.share_name == ""
        assert p.driver_name == ""

    def test_failed_query_adds_error(self):
        scanner = _make_scanner(printers=_json_fail("Access denied"))
        data = scanner.scan()
        assert any("Get-Printer" in e for e in data.errors)

    def test_failed_query_returns_empty_list(self):
        scanner = _make_scanner(printers=_json_fail())
        data = scanner.scan()
        assert data.printers == ()


# ── Print jobs ─────────────────────────────────────────────────────────────────

class TestGetPrintJobs:
    def test_single_job_as_dict(self):
        printers_resp = _json_ok([_printer_item()])
        jobs_resp = _json_ok(_job_item())
        scanner = _make_scanner(printers=printers_resp, jobs=jobs_resp)
        data = scanner.scan()
        assert len(data.print_jobs) == 1

    def test_multiple_jobs(self):
        printers_resp = _json_ok([_printer_item()])
        jobs_resp = _json_ok([_job_item(1), _job_item(2), _job_item(3)])
        scanner = _make_scanner(printers=printers_resp, jobs=jobs_resp)
        data = scanner.scan()
        assert len(data.print_jobs) == 3

    def test_job_fields_mapped(self):
        printers_resp = _json_ok([_printer_item()])
        jobs_resp = _json_ok(_job_item(
            job_id=42, printer="HP LaserJet",
            DocumentName="Budget.xlsx", UserName="radovan",
            TotalPages=8, JobStatus="Error"
        ))
        scanner = _make_scanner(printers=printers_resp, jobs=jobs_resp)
        data = scanner.scan()
        j = data.print_jobs[0]
        assert j.job_id == 42
        assert j.printer_name == "HP LaserJet"
        assert j.document_name == "Budget.xlsx"
        assert j.user_name == "radovan"
        assert j.total_pages == 8
        assert j.status == "Error"

    def test_no_jobs_is_not_error(self):
        """Empty job queue is normal — must not add to errors."""
        printers_resp = _json_ok([_printer_item()])
        scanner = _make_scanner(printers=printers_resp, jobs=_json_ok(None))
        data = scanner.scan()
        assert data.print_jobs == ()
        assert data.errors == ()

    def test_job_stderr_adds_error(self):
        printers_resp = _json_ok([_printer_item()])
        scanner = _make_scanner(printers=printers_resp, jobs=_json_fail("RPC error"))
        data = scanner.scan()
        assert any("Get-PrintJob" in e for e in data.errors)

    def test_null_total_pages_handled(self):
        printers_resp = _json_ok([_printer_item()])
        jobs_resp = _json_ok(_job_item(TotalPages=None))
        scanner = _make_scanner(printers=printers_resp, jobs=jobs_resp)
        data = scanner.scan()
        assert data.print_jobs[0].total_pages is None
