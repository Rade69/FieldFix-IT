from app.core.issue import Issue
from app.core.risk_level import RiskLevel


def test_construct_with_required_fields_only():
    issue = Issue(id="smb_6118", title="Workgroup server list unavailable", severity=RiskLevel.MEDIUM)
    assert issue.evidence == []
    assert issue.recommended_actions == []
    assert issue.confidence == "Medium"
    assert issue.related_module == ""


def test_construct_with_full_fields():
    issue = Issue(
        id="smb_6118",
        title="Workgroup server list unavailable",
        severity=RiskLevel.MEDIUM,
        evidence=["net view returned 6118", "direct IP access works"],
        likely_cause="Network Discovery disabled",
        confidence="High",
        recommended_actions=["enable_network_discovery"],
        related_module="smb",
    )
    assert issue.severity == RiskLevel.MEDIUM
    assert "direct IP access works" in issue.evidence
