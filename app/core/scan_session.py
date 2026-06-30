"""ScanSession — orchestrates a full diagnostic scan across all modules.

Introduced in Faza 11 (Dashboard v2) as the shared coordinator for Dashboard.
Individual module pages still run their own scanners independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from app.core.decision_engine import DecisionEngine
from app.core.issue import Issue
from app.core.powershell_runner import PowerShellRunner
from app.modules.network.scanner import NetworkScanner
from app.modules.printers.scanner import PrintersScanner
from app.modules.services.scanner import ServicesScanner
from app.modules.smb.scanner import SmbScanner
from app.reports.models import ScanReport


@dataclass(frozen=True)
class ScanResult:
    report: ScanReport
    issues: tuple[Issue, ...]
    scanned_at: str  # ISO 8601


class ScanSession:
    """Runs Network, SMB, Services and Printers scanners then Decision Engine."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def run(
        self,
        smb_target_ip: str = "",
        on_progress: Callable[[str], None] | None = None,
    ) -> ScanResult:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        def _prog(msg: str) -> None:
            if on_progress:
                on_progress(msg)

        _prog("Scanning Network…")
        network = NetworkScanner(self._runner).scan()

        _prog("Scanning SMB…")
        smb = SmbScanner(self._runner).scan(target_ip=smb_target_ip)

        _prog("Scanning Services…")
        services = ServicesScanner(self._runner).scan()

        _prog("Scanning Printers…")
        printers = PrintersScanner(self._runner).scan()

        _prog("Analyzing…")
        hostname = network.hostname if network else ""
        report = ScanReport(
            generated_at=ts,
            hostname=hostname,
            network=network,
            smb=smb,
            services=services,
            printers=printers,
        )
        issues = DecisionEngine().analyze(report)
        return ScanResult(report=report, issues=issues, scanned_at=ts)
