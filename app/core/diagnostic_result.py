from dataclasses import dataclass, field

from app.core.issue import Issue
from app.core.recommendation import Recommendation
from app.core.scan_status import ScanStatus


@dataclass(frozen=True)
class DiagnosticResult:
    """Aggregated outcome of one module's scan (e.g. Network, SMB, Firewall)."""

    module: str
    status: ScanStatus
    issues: list[Issue] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
