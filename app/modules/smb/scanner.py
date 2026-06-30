import time

from app.core.powershell_runner import PowerShellRunner
from app.modules.smb import net_view_parser
from app.modules.smb.models import (
    NetViewEntry,
    PortCheckResult,
    SmbClientConfig,
    SmbData,
    SmbServerConfig,
    SmbShare,
)

# Human-readable hints for known net view / SMB error codes.
# These are UI helpers only — the full knowledge base lives in app/knowledge/smb/.
NET_VIEW_ERROR_HINTS: dict[int, str] = {
    53: "Network path not found — check IP address, firewall (port 445), and routing.",
    64: "Network name no longer available — SMB session dropped, check firewall rules.",
    6118: "Server list unavailable — Network Discovery may be off or Computer Browser stopped.",
    1272: "Guest access blocked — EnableInsecureGuestLogons is disabled on this client.",
    5: "Access denied — verify share permissions and user account.",
    86: "Wrong network password — check username and password.",
    1326: "Logon failure — unknown username or bad password.",
}


def _bool_from_json(data: object, key: str) -> bool | None:
    if isinstance(data, dict):
        v = data.get(key)
        if isinstance(v, bool):
            return v
    return None


class SmbScanner:
    """Collects SMB diagnostics via PowerShell. Read-only — no Windows settings changed."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def scan(self, target_ip: str = "") -> SmbData:
        """Run all SMB checks. target_ip enables port-445 test and net view."""
        start = time.monotonic()
        errors: list[str] = []

        server_config = self._get_server_config(errors)
        client_config = self._get_client_config(errors)
        shares = self._get_shares(errors)

        port_445: PortCheckResult | None = None
        net_view_success: bool | None = None
        net_view_entries: list[NetViewEntry] = []
        net_view_error_code: int | None = None

        if target_ip:
            port_445 = self._check_port_445(target_ip, errors)
            net_view_success, net_view_entries, net_view_error_code = self._net_view(
                target_ip, errors
            )

        return SmbData(
            server_config=server_config,
            client_config=client_config,
            shares=tuple(shares),
            port_445=port_445,
            net_view_success=net_view_success,
            net_view_entries=tuple(net_view_entries),
            net_view_error_code=net_view_error_code,
            scan_duration_ms=(time.monotonic() - start) * 1000,
            errors=tuple(errors),
        )

    # ------------------------------------------------------------------ private

    def _get_server_config(self, errors: list[str]) -> SmbServerConfig | None:
        cmd = (
            "Get-SmbServerConfiguration | "
            "Select-Object EnableSMB1Protocol, EnableSMB2Protocol, "
            "RequireSecuritySignature, EnableSecuritySignature | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-SmbServerConfiguration: {result.stderr or 'no output'}")
            return None
        d = result.parsed_json
        return SmbServerConfig(
            smb1_enabled=_bool_from_json(d, "EnableSMB1Protocol"),
            smb2_enabled=_bool_from_json(d, "EnableSMB2Protocol"),
            require_security_signature=_bool_from_json(d, "RequireSecuritySignature"),
            enable_security_signature=_bool_from_json(d, "EnableSecuritySignature"),
        )

    def _get_client_config(self, errors: list[str]) -> SmbClientConfig | None:
        cmd = (
            "Get-SmbClientConfiguration | "
            "Select-Object EnableInsecureGuestLogons, RequireSecuritySignature, "
            "EnableSecuritySignature | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-SmbClientConfiguration: {result.stderr or 'no output'}")
            return None
        d = result.parsed_json
        return SmbClientConfig(
            enable_insecure_guest_logons=_bool_from_json(d, "EnableInsecureGuestLogons"),
            require_security_signature=_bool_from_json(d, "RequireSecuritySignature"),
            enable_security_signature=_bool_from_json(d, "EnableSecuritySignature"),
        )

    def _get_shares(self, errors: list[str]) -> list[SmbShare]:
        cmd = (
            "Get-SmbShare | "
            "Select-Object Name, Path, Description, ShareType | "
            "ConvertTo-Json -Compress"
        )
        result = self._runner.run_json(cmd, timeout=15)
        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-SmbShare: {result.stderr or 'no output'}")
            return []
        raw = result.parsed_json
        if isinstance(raw, dict):
            raw = [raw]
        return [
            SmbShare(
                name=str(item.get("Name", "")),
                path=str(item.get("Path", "") or ""),
                description=str(item.get("Description", "") or ""),
                share_type=str(item.get("ShareType", "") or ""),
            )
            for item in raw
            if isinstance(item, dict)
        ]

    def _check_port_445(self, target_ip: str, errors: list[str]) -> PortCheckResult:
        cmd = (
            f"(Test-NetConnection -ComputerName '{target_ip}' -Port 445 "
            f"-WarningAction SilentlyContinue -InformationLevel Quiet) | ConvertTo-Json"
        )
        result = self._runner.run_json(cmd, timeout=12)
        if result.succeeded and result.parsed_json is not None:
            return PortCheckResult(
                target_ip=target_ip, port=445, reachable=bool(result.parsed_json)
            )
        errors.append(f"Port 445 check failed for {target_ip}: {result.stderr or 'timeout'}")
        return PortCheckResult(
            target_ip=target_ip, port=445, reachable=None,
            error=result.stderr or "command failed",
        )

    def _net_view(
        self, target_ip: str, errors: list[str]
    ) -> tuple[bool, list[NetViewEntry], int | None]:
        """Run 'net view \\\\target_ip' and parse output. Returns (success, entries, error_code)."""
        result = self._runner.run(
            f"net view \\\\{target_ip} 2>&1", timeout=20
        )

        if result.succeeded:
            entries = net_view_parser.parse_shares(result.stdout)
            return True, entries, None

        error_code = net_view_parser.parse_error_code(result.stdout or result.stderr)
        if error_code:
            hint = NET_VIEW_ERROR_HINTS.get(error_code, "")
            errors.append(
                f"net view error {error_code}: {hint}" if hint
                else f"net view failed (error {error_code})"
            )
        else:
            errors.append(f"net view \\\\{target_ip} failed: {result.stderr or result.stdout}")
        return False, [], error_code
