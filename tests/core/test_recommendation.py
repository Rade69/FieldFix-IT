from app.core.recommendation import Recommendation
from app.core.risk_level import RiskLevel


def test_construct_minimal():
    rec = Recommendation(title="Enable Network Discovery", risk_level=RiskLevel.LOW, action_id="enable_network_discovery")
    assert rec.can_apply is True
    assert rec.requires_admin is False
    assert rec.reason_if_not_applicable is None
    assert rec.what_it_changes == []


def test_not_applicable_reason():
    rec = Recommendation(
        title="Enable SMB1",
        risk_level=RiskLevel.HIGH,
        action_id="enable_smb1",
        can_apply=False,
        reason_if_not_applicable="Danger Zone action requires explicit confirmation first",
    )
    assert rec.can_apply is False
    assert rec.reason_if_not_applicable is not None
