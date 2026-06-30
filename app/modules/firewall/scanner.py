import time

from app.core.powershell_runner import PowerShellRunner
from app.modules.firewall.models import FirewallData, FirewallProfile, FirewallRule


def _as_list(data: object) -> list:
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


class FirewallScanner:
    """Collects Windows Firewall diagnostics. Read-only - no settings are changed."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def scan(self) -> FirewallData:
        start = time.monotonic()
        errors: list[str] = []

        profiles = self._get_profiles(errors)
        file_sharing_rules = self._get_rules("File and Printer Sharing", errors)
        network_discovery_rules = self._get_rules("Network Discovery", errors)

        return FirewallData(
            profiles=tuple(profiles),
            file_sharing_rules=tuple(file_sharing_rules),
            network_discovery_rules=tuple(network_discovery_rules),
            scan_duration_ms=(time.monotonic() - start) * 1000,
            errors=tuple(errors),
        )

    def _get_profiles(self, errors: list[str]) -> list[FirewallProfile]:
        cmd = (
            "Get-NetFirewallProfile | "
            "Select-Object Name, Enabled, "
            "@{N='DefaultInboundAction';E={$_.DefaultInboundAction.ToString()}}, "
            "@{N='DefaultOutboundAction';E={$_.DefaultOutboundAction.ToString()}} | "
            "ConvertTo-Json -Compress"
        )
        try:
            result = self._runner.run_json(cmd, timeout=20)
        except Exception as exc:
            errors.append(f"Get-NetFirewallProfile: {exc}")
            return []

        if not result.succeeded or result.parsed_json is None:
            errors.append(f"Get-NetFirewallProfile: {result.stderr or 'no output'}")
            return []

        profiles: list[FirewallProfile] = []
        for item in _as_list(result.parsed_json):
            if not isinstance(item, dict):
                continue
            profiles.append(FirewallProfile(
                name=str(item.get("Name", "")),
                enabled=_bool_or_none(item.get("Enabled")),
                default_inbound=str(item.get("DefaultInboundAction", "") or ""),
                default_outbound=str(item.get("DefaultOutboundAction", "") or ""),
            ))
        return profiles

    def _get_rules(self, group: str, errors: list[str]) -> list[FirewallRule]:
        cmd = (
            f"Get-NetFirewallRule -DisplayGroup \"{group}\" -ErrorAction SilentlyContinue | "
            "Select-Object Name, DisplayName, "
            "@{N='Direction';E={$_.Direction.ToString()}}, "
            "@{N='Action';E={$_.Action.ToString()}}, "
            "Enabled, "
            "@{N='Profile';E={$_.Profile.ToString()}} | "
            "ConvertTo-Json -Compress"
        )
        try:
            result = self._runner.run_json(cmd, timeout=20)
        except Exception as exc:
            errors.append(f"Get-NetFirewallRule ({group}): {exc}")
            return []

        if not result.succeeded:
            errors.append(f"Get-NetFirewallRule ({group}): {result.stderr or 'no output'}")
            return []
        if result.parsed_json is None:
            return []

        rules: list[FirewallRule] = []
        for item in _as_list(result.parsed_json):
            if not isinstance(item, dict):
                continue
            rules.append(FirewallRule(
                name=str(item.get("Name", "")),
                display_name=str(item.get("DisplayName", "") or ""),
                direction=str(item.get("Direction", "") or ""),
                action=str(item.get("Action", "") or ""),
                enabled=_bool_or_none(item.get("Enabled")),
                profile=str(item.get("Profile", "") or ""),
            ))
        return rules
