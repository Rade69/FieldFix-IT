from unittest.mock import MagicMock

from app.core.command_result import CommandResult
from app.modules.firewall.models import FirewallData
from app.modules.firewall.scanner import FirewallScanner


def _json_ok(data: object) -> CommandResult:
    return CommandResult(command="cmd", stdout="...", exit_code=0, parsed_json=data)


def _json_fail(stderr: str = "err") -> CommandResult:
    return CommandResult(command="cmd", exit_code=1, stderr=stderr)


def _make_scanner(profiles=None, file_rules=None, net_rules=None) -> FirewallScanner:
    runner = MagicMock()
    runner.run_json.side_effect = [
        profiles or _json_fail(),
        file_rules or _json_fail(),
        net_rules or _json_fail(),
    ]
    return FirewallScanner(runner)


def _profile(name: str = "Private", enabled: bool = True) -> dict:
    return {
        "Name": name,
        "Enabled": enabled,
        "DefaultInboundAction": "Block",
        "DefaultOutboundAction": "Allow",
    }


def _rule(name: str = "FPS-SMB-In-TCP", enabled: bool = True) -> dict:
    return {
        "Name": name,
        "DisplayName": "File and Printer Sharing (SMB-In)",
        "Direction": "Inbound",
        "Action": "Allow",
        "Enabled": enabled,
        "Profile": "Private",
    }


class TestFirewallScan:
    def test_returns_firewall_data(self):
        scanner = _make_scanner()

        assert isinstance(scanner.scan(), FirewallData)

    def test_duration_non_negative(self):
        scanner = _make_scanner()

        assert scanner.scan().scan_duration_ms >= 0

    def test_all_failures_do_not_raise(self):
        scanner = _make_scanner(_json_fail("profiles"), _json_fail("file"), _json_fail("net"))

        data = scanner.scan()

        assert isinstance(data, FirewallData)
        assert len(data.errors) == 3


class TestProfiles:
    def test_profiles_are_parsed(self):
        scanner = _make_scanner(
            profiles=_json_ok([_profile("Domain"), _profile("Private"), _profile("Public")]),
            file_rules=_json_ok([]),
            net_rules=_json_ok([]),
        )

        data = scanner.scan()

        assert [p.name for p in data.profiles] == ["Domain", "Private", "Public"]
        assert data.profiles[0].enabled is True
        assert data.profiles[0].default_inbound == "Block"
        assert data.profiles[0].default_outbound == "Allow"

    def test_single_profile_dict_is_normalized(self):
        scanner = _make_scanner(
            profiles=_json_ok(_profile("Private")),
            file_rules=_json_ok([]),
            net_rules=_json_ok([]),
        )

        data = scanner.scan()

        assert len(data.profiles) == 1
        assert data.profiles[0].name == "Private"

    def test_enabled_false_maps_correctly(self):
        scanner = _make_scanner(
            profiles=_json_ok(_profile("Public", enabled=False)),
            file_rules=_json_ok([]),
            net_rules=_json_ok([]),
        )

        data = scanner.scan()

        assert data.profiles[0].enabled is False

    def test_profiles_error_is_recorded_and_rules_continue(self):
        scanner = _make_scanner(
            profiles=_json_fail("access denied"),
            file_rules=_json_ok(_rule()),
            net_rules=_json_ok(_rule("ND-In")),
        )

        data = scanner.scan()

        assert data.profiles == ()
        assert len(data.file_sharing_rules) == 1
        assert len(data.network_discovery_rules) == 1
        assert any("Get-NetFirewallProfile" in e for e in data.errors)


class TestRules:
    def test_rule_fields_are_parsed(self):
        scanner = _make_scanner(
            profiles=_json_ok([]),
            file_rules=_json_ok(_rule()),
            net_rules=_json_ok([]),
        )

        data = scanner.scan()
        rule = data.file_sharing_rules[0]

        assert rule.name == "FPS-SMB-In-TCP"
        assert rule.display_name == "File and Printer Sharing (SMB-In)"
        assert rule.direction == "Inbound"
        assert rule.action == "Allow"
        assert rule.enabled is True
        assert rule.profile == "Private"

    def test_single_rule_dict_is_normalized(self):
        scanner = _make_scanner(
            profiles=_json_ok([]),
            file_rules=_json_ok(_rule("Single")),
            net_rules=_json_ok([]),
        )

        data = scanner.scan()

        assert len(data.file_sharing_rules) == 1
        assert data.file_sharing_rules[0].name == "Single"

    def test_multiple_rules_list_is_parsed(self):
        scanner = _make_scanner(
            profiles=_json_ok([]),
            file_rules=_json_ok([_rule("One"), _rule("Two", enabled=False)]),
            net_rules=_json_ok([]),
        )

        data = scanner.scan()

        assert [r.name for r in data.file_sharing_rules] == ["One", "Two"]
        assert data.file_sharing_rules[1].enabled is False

    def test_file_sharing_error_is_recorded_and_others_continue(self):
        scanner = _make_scanner(
            profiles=_json_ok(_profile()),
            file_rules=_json_fail("rule error"),
            net_rules=_json_ok(_rule("ND-In")),
        )

        data = scanner.scan()

        assert len(data.profiles) == 1
        assert data.file_sharing_rules == ()
        assert len(data.network_discovery_rules) == 1
        assert any("File and Printer Sharing" in e for e in data.errors)

    def test_empty_rule_list_returns_empty_tuple(self):
        scanner = _make_scanner(
            profiles=_json_ok(_profile()),
            file_rules=_json_ok([]),
            net_rules=_json_ok([]),
        )

        data = scanner.scan()

        assert data.file_sharing_rules == ()
        assert data.network_discovery_rules == ()

    def test_none_rule_json_on_success_is_empty_not_error(self):
        scanner = _make_scanner(
            profiles=_json_ok(_profile()),
            file_rules=_json_ok(None),
            net_rules=_json_ok(None),
        )

        data = scanner.scan()

        assert data.file_sharing_rules == ()
        assert data.network_discovery_rules == ()
        assert data.errors == ()
