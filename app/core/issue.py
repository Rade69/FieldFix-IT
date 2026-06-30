from dataclasses import dataclass, field

from app.core.risk_level import RiskLevel


@dataclass(frozen=True)
class Issue:
    """A diagnostic finding surfaced to the user, with evidence and a likely cause."""

    id: str
    title: str
    severity: RiskLevel
    evidence: list[str] = field(default_factory=list)
    likely_cause: str = ""
    confidence: str = "Medium"  # "High" | "Medium" | "Low" — see Faza 10 Decision Engine
    recommended_actions: list[str] = field(default_factory=list)
    related_module: str = ""
