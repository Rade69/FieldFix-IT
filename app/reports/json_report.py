from __future__ import annotations

import dataclasses
import json

from app.core.issue import Issue
from app.reports.models import ScanReport


def _issue_to_dict(issue: Issue) -> dict:
    return {
        "id": issue.id,
        "title": issue.title,
        "severity": str(issue.severity),   # "HIGH", "MEDIUM", etc. via RiskLevel.__str__
        "likely_cause": issue.likely_cause,
        "confidence": issue.confidence,
        "evidence": issue.evidence,
        "recommended_actions": issue.recommended_actions,
        "related_module": issue.related_module,
    }


def write_json(report: ScanReport, issues: tuple[Issue, ...] = ()) -> str:
    """Serialize ScanReport (+ optional issues) to indented JSON."""
    data = dataclasses.asdict(report)
    if issues:
        data["issues"] = [_issue_to_dict(i) for i in issues]
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)
