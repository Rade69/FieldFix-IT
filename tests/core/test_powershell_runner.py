import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.core.powershell_runner import PowerShellRunner, is_admin


@pytest.fixture
def runner():
    return PowerShellRunner()


def _mock_proc(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


class TestRun:
    def test_success_sets_stdout_and_exit_code(self, runner):
        with patch("subprocess.run", return_value=_mock_proc(stdout="hello\n")):
            result = runner.run("echo hello")
        assert result.succeeded
        assert result.stdout == "hello"
        assert result.exit_code == 0
        assert not result.timed_out

    def test_nonzero_exit_code_is_not_succeeded(self, runner):
        with patch("subprocess.run", return_value=_mock_proc(returncode=1, stderr="Access denied")):
            result = runner.run("exit 1")
        assert not result.succeeded
        assert result.exit_code == 1
        assert result.stderr == "Access denied"

    def test_stdout_is_stripped_raw_output_is_not(self, runner):
        with patch("subprocess.run", return_value=_mock_proc(stdout="  spaced  \n")):
            result = runner.run("echo spaced")
        assert result.stdout == "spaced"
        assert result.raw_output == "  spaced  \n"

    def test_timeout_sets_timed_out_flag(self, runner):
        exc = subprocess.TimeoutExpired(cmd=["powershell.exe"], timeout=0.01)
        exc.stdout = b""
        exc.stderr = b""
        with patch("subprocess.run", side_effect=exc):
            result = runner.run("Start-Sleep -Seconds 60", timeout=0)
        assert result.timed_out
        assert not result.succeeded
        assert result.exit_code is None

    def test_duration_ms_is_non_negative(self, runner):
        with patch("subprocess.run", return_value=_mock_proc()):
            result = runner.run("echo x")
        assert result.duration_ms >= 0

    def test_command_is_stored(self, runner):
        cmd = "Get-NetAdapter | ConvertTo-Json"
        with patch("subprocess.run", return_value=_mock_proc()):
            result = runner.run(cmd)
        assert result.command == cmd

    def test_timeout_stdout_bytes_decoded(self, runner):
        exc = subprocess.TimeoutExpired(cmd=["powershell.exe"], timeout=0.01)
        exc.stdout = b"partial output"
        exc.stderr = b""
        with patch("subprocess.run", side_effect=exc):
            result = runner.run("long-cmd", timeout=0)
        assert result.timed_out
        assert result.raw_output == "partial output"


class TestRunJson:
    def test_parses_valid_json_list(self, runner):
        payload = [{"Name": "Ethernet", "Status": "Up"}]
        with patch("subprocess.run", return_value=_mock_proc(stdout=json.dumps(payload))):
            result = runner.run_json("Get-NetAdapter | ConvertTo-Json")
        assert result.succeeded
        assert result.parsed_json == payload

    def test_parses_valid_json_dict(self, runner):
        payload = {"Enabled": True, "Profile": "Private"}
        with patch("subprocess.run", return_value=_mock_proc(stdout=json.dumps(payload))):
            result = runner.run_json("Get-NetConnectionProfile | ConvertTo-Json")
        assert result.parsed_json == payload

    def test_invalid_json_leaves_parsed_json_none(self, runner):
        with patch("subprocess.run", return_value=_mock_proc(stdout="not json output")):
            result = runner.run_json("some-legacy-command")
        assert result.parsed_json is None
        assert result.succeeded

    def test_failed_command_leaves_parsed_json_none(self, runner):
        with patch("subprocess.run", return_value=_mock_proc(returncode=1, stderr="error")):
            result = runner.run_json("bad-command")
        assert result.parsed_json is None
        assert not result.succeeded

    def test_empty_stdout_leaves_parsed_json_none(self, runner):
        with patch("subprocess.run", return_value=_mock_proc(stdout="")):
            result = runner.run_json("empty-output-command")
        assert result.parsed_json is None

    def test_original_result_fields_preserved(self, runner):
        payload = {"x": 1}
        with patch("subprocess.run", return_value=_mock_proc(stdout=json.dumps(payload), stderr="warn")):
            result = runner.run_json("cmd")
        assert result.stderr == "warn"
        assert result.exit_code == 0


class TestIsAdmin:
    def test_returns_bool(self):
        assert isinstance(is_admin(), bool)

    def test_mocked_admin_true(self):
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
            assert is_admin() is True

    def test_mocked_non_admin(self):
        with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
            assert is_admin() is False

    def test_exception_returns_false(self):
        with patch("ctypes.windll.shell32.IsUserAnAdmin", side_effect=OSError):
            assert is_admin() is False
