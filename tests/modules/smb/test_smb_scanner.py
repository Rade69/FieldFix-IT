from unittest.mock import MagicMock

import pytest

from app.core.command_result import CommandResult
from app.modules.smb.models import SmbData
from app.modules.smb.scanner import SmbScanner

# --------------------------------------------------------------------------- helpers


def _json_ok(data: object) -> CommandResult:
    return CommandResult(command="cmd", stdout="...", exit_code=0, parsed_json=data)


def _json_fail(stderr: str = "err") -> CommandResult:
    return CommandResult(command="cmd", exit_code=1, stderr=stderr)


def _run_ok(stdout: str = "") -> CommandResult:
    return CommandResult(command="cmd", stdout=stdout, exit_code=0)


def _run_fail(stdout: str = "", stderr: str = "") -> CommandResult:
    return CommandResult(command="cmd", stdout=stdout, stderr=stderr, exit_code=1)


def _make_scanner(run_json_side=None, run_return=None) -> SmbScanner:
    runner = MagicMock()
    if run_json_side is not None:
        runner.run_json.side_effect = run_json_side
    else:
        runner.run_json.return_value = _json_fail()
    runner.run.return_value = run_return or _run_ok()
    return SmbScanner(runner)


def _null_side(n: int, overrides: dict | None = None) -> list:
    overrides = overrides or {}
    return [overrides.get(i, _json_fail()) for i in range(n)]


# --------------------------------------------------------------------------- tests


class TestScanReturnsData:
    def test_returns_smb_data(self):
        scanner = _make_scanner()
        assert isinstance(scanner.scan(), SmbData)

    def test_duration_non_negative(self):
        scanner = _make_scanner()
        assert scanner.scan().scan_duration_ms >= 0

    def test_no_target_ip_skips_port_and_net_view(self):
        scanner = _make_scanner()
        data = scanner.scan()
        assert data.port_445 is None
        assert data.net_view_success is None


class TestServerConfig:
    _CFG = {
        "EnableSMB1Protocol": False,
        "EnableSMB2Protocol": True,
        "RequireSecuritySignature": False,
        "EnableSecuritySignature": True,
    }

    def test_server_config_parsed(self):
        scanner = _make_scanner(run_json_side=_null_side(3, {0: _json_ok(self._CFG)}))
        data = scanner.scan()
        assert data.server_config is not None
        assert data.server_config.smb1_enabled is False
        assert data.server_config.smb2_enabled is True

    def test_failed_config_returns_none_and_error(self):
        scanner = _make_scanner(run_json_side=_null_side(3))
        data = scanner.scan()
        assert data.server_config is None
        assert any("Get-SmbServerConfiguration" in e for e in data.errors)


class TestClientConfig:
    _CFG = {
        "EnableInsecureGuestLogons": False,
        "RequireSecuritySignature": False,
        "EnableSecuritySignature": True,
    }

    def test_client_config_parsed(self):
        scanner = _make_scanner(run_json_side=_null_side(3, {1: _json_ok(self._CFG)}))
        data = scanner.scan()
        assert data.client_config is not None
        assert data.client_config.enable_insecure_guest_logons is False

    def test_failed_client_config_adds_error(self):
        scanner = _make_scanner(run_json_side=_null_side(3))
        data = scanner.scan()
        assert any("Get-SmbClientConfiguration" in e for e in data.errors)


class TestShares:
    _SHARES = [
        {"Name": "docs", "Path": "C:\\docs", "Description": "", "ShareType": "FileSystemDirectory"},
        {"Name": "IPC$", "Path": "", "Description": "Remote IPC", "ShareType": "Ipc"},
    ]

    def test_shares_parsed(self):
        scanner = _make_scanner(run_json_side=_null_side(3, {2: _json_ok(self._SHARES)}))
        data = scanner.scan()
        assert len(data.shares) == 2
        assert data.shares[0].name == "docs"
        assert data.shares[0].path == "C:\\docs"

    def test_single_share_as_dict(self):
        single = self._SHARES[0]
        scanner = _make_scanner(run_json_side=_null_side(3, {2: _json_ok(single)}))
        data = scanner.scan()
        assert len(data.shares) == 1

    def test_failed_shares_adds_error(self):
        scanner = _make_scanner(run_json_side=_null_side(3))
        data = scanner.scan()
        assert any("Get-SmbShare" in e for e in data.errors)


class TestPort445:
    # With target_ip: run_json calls are server(0), client(1), shares(2), port(3)
    def test_port_reachable(self):
        scanner = _make_scanner(
            run_json_side=_null_side(4, {3: _json_ok(True)}),
            run_return=_run_ok(),
        )
        data = scanner.scan(target_ip="192.168.1.100")
        assert data.port_445 is not None
        assert data.port_445.reachable is True
        assert data.port_445.target_ip == "192.168.1.100"
        assert data.port_445.port == 445

    def test_port_unreachable(self):
        scanner = _make_scanner(
            run_json_side=_null_side(4, {3: _json_ok(False)}),
            run_return=_run_ok(),
        )
        data = scanner.scan(target_ip="10.0.0.99")
        assert data.port_445.reachable is False

    def test_port_check_failed_sets_none(self):
        scanner = _make_scanner(
            run_json_side=_null_side(4),
            run_return=_run_ok(),
        )
        data = scanner.scan(target_ip="10.0.0.99")
        assert data.port_445.reachable is None
        assert any("Port 445" in e for e in data.errors)


class TestNetView:
    _NET_VIEW_SUCCESS = (
        "Shared resources at \\\\192.168.1.100\n\n"
        "Share name  Type  Used as  Comment\n\n"
        "----------------------------------------------\n"
        "docs        Disk\n"
        "The command completed successfully.\n"
    )
    _NET_VIEW_ERROR_53 = "System error 53 has occurred.\nThe network path was not found.\n"

    def test_net_view_success(self):
        scanner = _make_scanner(
            run_json_side=_null_side(4),
            run_return=_run_ok(stdout=self._NET_VIEW_SUCCESS),
        )
        data = scanner.scan(target_ip="192.168.1.100")
        assert data.net_view_success is True
        assert len(data.net_view_entries) == 1
        assert data.net_view_entries[0].name == "docs"

    def test_net_view_error_53_captured(self):
        scanner = _make_scanner(
            run_json_side=_null_side(4),
            run_return=_run_fail(stdout=self._NET_VIEW_ERROR_53),
        )
        data = scanner.scan(target_ip="192.168.1.100")
        assert data.net_view_success is False
        assert data.net_view_error_code == 53
        assert any("53" in e for e in data.errors)

    def test_net_view_not_run_without_target_ip(self):
        scanner = _make_scanner()
        data = scanner.scan()
        assert data.net_view_success is None
        assert data.net_view_entries == ()
