from unittest.mock import MagicMock

import pytest

from app.core.command_result import CommandResult
from app.modules.services.models import ServicesData
from app.modules.services.scanner import MONITORED_SERVICES, ServicesScanner, _normalize, _STATUS_MAP, _START_TYPE_MAP


def _json_ok(data: object) -> CommandResult:
    return CommandResult(command="cmd", stdout="...", exit_code=0, parsed_json=data)


def _json_fail(stderr: str = "err") -> CommandResult:
    return CommandResult(command="cmd", exit_code=1, stderr=stderr)


def _make_scanner(json_return=None) -> ServicesScanner:
    runner = MagicMock()
    runner.run_json.return_value = json_return or _json_fail()
    return ServicesScanner(runner)


def _service_item(name: str, status: str = "Running", start_type: str = "Automatic") -> dict:
    return {
        "Name": name,
        "DisplayName": f"{name} Display",
        "Status": status,
        "StartType": start_type,
    }


def _all_services_json(status: str = "Running") -> list[dict]:
    return [_service_item(name, status) for name in MONITORED_SERVICES]


class TestNormalizeHelper:
    def test_int_status_mapped(self):
        assert _normalize(4, _STATUS_MAP) == "Running"
        assert _normalize(1, _STATUS_MAP) == "Stopped"

    def test_string_passthrough(self):
        assert _normalize("Running", _STATUS_MAP) == "Running"

    def test_unknown_int_stringified(self):
        assert _normalize(99, _STATUS_MAP) == "99"

    def test_none_returns_empty(self):
        assert _normalize(None, _STATUS_MAP) == ""

    def test_start_type_int_mapped(self):
        assert _normalize(2, _START_TYPE_MAP) == "Automatic"
        assert _normalize(4, _START_TYPE_MAP) == "Disabled"


class TestScanReturnsData:
    def test_returns_services_data(self):
        scanner = _make_scanner()
        assert isinstance(scanner.scan(), ServicesData)

    def test_duration_non_negative(self):
        scanner = _make_scanner()
        assert scanner.scan().scan_duration_ms >= 0


class TestGetServices:
    def test_all_services_parsed(self):
        scanner = _make_scanner(_json_ok(_all_services_json()))
        data = scanner.scan()
        assert len(data.services) == len(MONITORED_SERVICES)

    def test_single_service_as_dict(self):
        scanner = _make_scanner(_json_ok(_service_item("Spooler")))
        data = scanner.scan()
        spooler = next((s for s in data.services if s.name == "Spooler"), None)
        assert spooler is not None
        assert spooler.status == "Running"

    def test_service_fields_populated(self):
        scanner = _make_scanner(_json_ok(_all_services_json()))
        data = scanner.scan()
        lanman = next(s for s in data.services if s.name == "LanmanServer")
        assert lanman.display_name == "LanmanServer Display"
        assert lanman.status == "Running"
        assert lanman.start_type == "Automatic"
        assert "dijeljenje" in lanman.required_for.lower()

    def test_stopped_service_detected(self):
        items = _all_services_json()
        items[0]["Status"] = "Stopped"  # LanmanServer stopped
        scanner = _make_scanner(_json_ok(items))
        data = scanner.scan()
        lanman = next(s for s in data.services if s.name == "LanmanServer")
        assert lanman.status == "Stopped"

    def test_int_status_normalized(self):
        item = _service_item("Spooler")
        item["Status"] = 4  # Running as integer
        item["StartType"] = 2  # Automatic as integer
        scanner = _make_scanner(_json_ok(item))
        data = scanner.scan()
        spooler = next(s for s in data.services if s.name == "Spooler")
        assert spooler.status == "Running"
        assert spooler.start_type == "Automatic"

    def test_failed_query_adds_error(self):
        scanner = _make_scanner(_json_fail("Access denied"))
        data = scanner.scan()
        assert any("Get-Service" in e for e in data.errors)
        assert len(data.services) == 0

    def test_missing_service_reported(self):
        # Only 7 out of 8 services returned — Spooler missing
        items = [_service_item(n) for n in list(MONITORED_SERVICES.keys())[:-1]]
        scanner = _make_scanner(_json_ok(items))
        data = scanner.scan()
        assert any("Spooler" in e for e in data.errors)
        # Missing service still appears with NotFound status
        missing = next((s for s in data.services if s.name == "Spooler"), None)
        assert missing is not None
        assert missing.status == "NotFound"

    def test_services_in_defined_order(self):
        import random
        items = _all_services_json()
        random.shuffle(items)
        scanner = _make_scanner(_json_ok(items))
        data = scanner.scan()
        names = [s.name for s in data.services]
        expected_order = list(MONITORED_SERVICES.keys())
        assert names == expected_order
