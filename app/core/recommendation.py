from dataclasses import dataclass, field

from app.core.risk_level import RiskLevel


@dataclass(frozen=True)
class Recommendation:
    """A possible fix action. Display-only until Fix Mode (Faza 13) wires real execution.

    Dashboard must route to Review Fix / Fix Center, never call apply directly
    from this model (see docs/architecture_notes.md, "Dashboard: Review Fix, ne Apply").
    """

    title: str
    risk_level: RiskLevel
    action_id: str
    what_it_changes: list[str] = field(default_factory=list)
    what_it_does_not_change: list[str] = field(default_factory=list)
    requires_admin: bool = False
    can_apply: bool = True
    reason_if_not_applicable: str | None = None
