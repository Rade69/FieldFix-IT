import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.issue import Issue
from app.core.risk_level import RiskLevel
from app.gui.widgets.decision_assistant_widget import DecisionAssistantWidget


@pytest.fixture(scope="session")
def qapp_instance():
    app = QApplication.instance() or QApplication([])
    yield app


def _issue() -> Issue:
    return Issue(
        id="PORT_445_CLOSED",
        title="Port 445 not reachable on 192.168.1.24",
        severity=RiskLevel.HIGH,
        evidence=["Test-NetConnection 192.168.1.24:445 = False"],
        likely_cause="Firewall blocking port 445, or Server service stopped on target machine.",
        confidence="High",
        recommended_actions=["Enable File and Printer Sharing firewall rules."],
        related_module="smb",
    )


def test_open_details_button_shows_real_issue_details(qapp_instance, monkeypatch):
    shown = {}

    def fake_information(parent, title, text):
        shown["parent"] = parent
        shown["title"] = title
        shown["text"] = text

    monkeypatch.setattr(QMessageBox, "information", fake_information)
    widget = DecisionAssistantWidget()
    widget.update_data((_issue(),))

    widget._open_details_button.click()

    assert shown["parent"] is widget
    assert shown["title"] == "Decision details"
    assert "Port 445 not reachable on 192.168.1.24" in shown["text"]
    assert "Test-NetConnection 192.168.1.24:445 = False" in shown["text"]
    assert "Enable File and Printer Sharing firewall rules." in shown["text"]


def test_open_details_button_disabled_without_issue(qapp_instance):
    widget = DecisionAssistantWidget()

    assert not widget._open_details_button.isEnabled()


def test_update_data_without_issues_clears_current_issue(qapp_instance):
    widget = DecisionAssistantWidget()
    widget.update_data((_issue(),))

    widget.update_data(())

    assert not widget._open_details_button.isEnabled()
    assert widget._problem_label.text() == "No issues detected."
