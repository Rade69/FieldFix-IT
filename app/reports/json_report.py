import dataclasses
import json

from app.reports.models import ScanReport


def write_json(report: ScanReport) -> str:
    """Serialize ScanReport to indented JSON. Tuples become arrays; None stays null."""
    return json.dumps(
        dataclasses.asdict(report),
        indent=2,
        ensure_ascii=False,
        default=str,  # safety net for any unexpected non-serializable types
    )
