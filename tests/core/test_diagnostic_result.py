from app.core.diagnostic_result import DiagnosticResult
from app.core.issue import Issue
from app.core.recommendation import Recommendation
from app.core.risk_level import RiskLevel
from app.core.scan_status import ScanStatus


def test_construct_empty_result():
    result = DiagnosticResult(module="network", status=ScanStatus.OK)
    assert result.issues == []
    assert result.recommendations == []
    assert result.evidence == []


def test_construct_with_issue_and_recommendation():
    issue = Issue(id="net_no_gateway", title="Gateway unreachable", severity=RiskLevel.HIGH)
    rec = Recommendation(title="Check cable/adapter", risk_level=RiskLevel.LOW, action_id="check_adapter")
    result = DiagnosticResult(
        module="network",
        status=ScanStatus.CRITICAL,
        issues=[issue],
        recommendations=[rec],
        evidence=["Ping gateway 192.168.100.1 timed out"],
        duration_ms=120.5,
    )
    assert result.status == ScanStatus.CRITICAL
    assert result.issues[0].severity == RiskLevel.HIGH
    assert result.recommendations[0].action_id == "check_adapter"
