from app.core.risk_level import RiskLevel


def test_ordering():
    assert RiskLevel.LOW < RiskLevel.MEDIUM < RiskLevel.HIGH < RiskLevel.CRITICAL


def test_str_matches_name():
    assert str(RiskLevel.HIGH) == "HIGH"


def test_comparison_with_threshold():
    assert RiskLevel.CRITICAL >= RiskLevel.HIGH
    assert not (RiskLevel.LOW >= RiskLevel.MEDIUM)
