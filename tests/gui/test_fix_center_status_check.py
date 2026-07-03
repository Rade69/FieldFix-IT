import pytest
from PySide6.QtWidgets import QApplication

from app.core.command_result import CommandResult
from app.core.risk_level import RiskLevel
from app.gui.pages.fix_center_page import FixAction, _AVAILABLE_FIXES, _FixActionCard


@pytest.fixture(scope="session")
def qapp_instance():
    app = QApplication.instance() or QApplication([])
    yield app


class _Runner:
    def __init__(self, stdout: str = "False") -> None:
        self.calls: list[str] = []
        self._stdout = stdout

    def run(self, command: str, timeout: int = 0) -> CommandResult:
        del timeout
        self.calls.append(command)
        return CommandResult(command=command, stdout=self._stdout, exit_code=0)


def _action() -> FixAction:
    return FixAction(
        id="TEST",
        title="Test Fix",
        description="Test description",
        what_it_changes="Nothing in tests",
        risk_level=RiskLevel.LOW,
        requires_admin=True,
        ps_command="Set-Something",
        check_cmd="Get-Something",
    )


def test_available_fixes_define_status_checks():
    assert all(action.check_cmd for action in _AVAILABLE_FIXES)


def test_fix_card_hides_apply_when_already_active(qapp_instance):
    runner = _Runner(stdout="True")

    card = _FixActionCard(_action(), runner, is_admin=True)

    assert runner.calls == ["Get-Something"]
    assert card._result_label.text() == "✓ Already active"
    assert card._apply_btn.isHidden()


def test_fix_card_keeps_apply_when_not_active(qapp_instance):
    runner = _Runner(stdout="False")

    card = _FixActionCard(_action(), runner, is_admin=True)

    assert runner.calls == ["Get-Something"]
    assert not card._apply_btn.isHidden()
