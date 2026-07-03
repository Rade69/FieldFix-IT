import ctypes
import dataclasses
import json
import subprocess
import time
from typing import Any

from app.core.command_result import CommandResult

_PS_ARGS = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"]


def is_admin() -> bool:
    """Return True if the current process has Administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def restart_as_admin() -> None:
    """Relaunch this process with Administrator privileges via UAC.

    If user accepts the UAC prompt the current (non-elevated) process exits
    and a new elevated instance starts.  If the user cancels the UAC dialog
    the function returns without doing anything.

    Works for both PyInstaller exe (sys.frozen) and dev-mode python -m app.main.
    """
    import os
    import sys
    import time
    from pathlib import Path

    if getattr(sys, "frozen", False):
        # PyInstaller bundle: run the exe directly, same directory
        prog = sys.executable
        params = ""
        work_dir = str(Path(sys.executable).parent)
    else:
        # Dev mode: must run as "python -m app.main" from project root,
        # NOT as "python app/main.py" — the latter breaks relative imports.
        prog = sys.executable
        params = "-m app.main"
        # This file is app/core/powershell_runner.py → project root is 2 levels up
        work_dir = str(Path(__file__).resolve().parent.parent.parent)

    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", prog, params or None, work_dir, 1)
    if int(ret) > 32:
        # UAC accepted — give the new elevated process a moment to initialise
        time.sleep(0.4)
        os._exit(0)


# Context: agent_reports/2026-06-30_powershell-runner.md
class PowerShellRunner:
    """Executes read-only PowerShell commands and returns CommandResult objects.

    Scan-only: never changes Windows settings. Fix commands are not implemented
    here — they belong to the Fix Center (Faza 13) and require explicit user
    confirmation before any Apply call.

    JSON-first rule (see docs/architecture_notes.md):
      - run_json() for structured cmdlets that support ConvertTo-Json
      - run() for legacy text commands (net view, ping, arp, etc.)
    """

    def run(self, command: str, timeout: int = 30) -> CommandResult:
        """Execute a PowerShell command. Returns CommandResult with raw stdout/stderr."""
        start = time.monotonic()
        timed_out = False
        raw_stdout = ""
        stderr = ""
        exit_code: int | None = None

        try:
            proc = subprocess.run(
                _PS_ARGS + [command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            raw_stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            raw_stdout = _decode_bytes(exc.stdout)
            stderr = _decode_bytes(exc.stderr)

        duration_ms = (time.monotonic() - start) * 1000

        return CommandResult(
            command=command,
            stdout=raw_stdout.strip(),
            stderr=stderr.strip(),
            exit_code=exit_code,
            duration_ms=duration_ms,
            timed_out=timed_out,
            raw_output=raw_stdout,
        )

    def run_json(self, command: str, timeout: int = 30) -> CommandResult:
        """Execute a PowerShell command expecting JSON output (ConvertTo-Json).

        Returns CommandResult with parsed_json populated on success.
        parsed_json is None if the command failed, timed out, or stdout is
        not valid JSON — callers must always check result.succeeded first.
        """
        result = self.run(command, timeout=timeout)
        if not result.succeeded or not result.stdout:
            return result

        parsed: Any | None = None
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

        return dataclasses.replace(result, parsed_json=parsed)


def _decode_bytes(data: bytes | str | None) -> str:
    """Safely decode subprocess output that may be bytes, str, or None."""
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data
