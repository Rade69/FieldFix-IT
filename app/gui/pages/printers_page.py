from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.gui.styles import TEXT_SECONDARY, secondary_text_style
from app.gui.widgets.empty_state import info_banner
from app.modules.printers.models import PrintersData
from app.modules.printers.scanner import PrintersScanner

_STATUS_OK = {"Normal", "Printing"}
_STATUS_WARN = {"Paused", "Initializing", "WarmingUp", "Processing", "Busy", "IoActive"}

_JOB_OK = {"Normal", "Spooling", "Printing", "Printed"}
_JOB_WARN = {"Paused", "Restart", "BlockedDevq"}


def _status_color(status: str) -> str:
    if status in _STATUS_OK:
        return "#3fb950"
    if status in _STATUS_WARN:
        return "#d29922"
    if status:
        return "#f85149"   # Error, Offline, PaperJam, etc.
    return TEXT_SECONDARY


def _job_color(status: str) -> str:
    if status in _JOB_OK:
        return "#3fb950"
    if status in _JOB_WARN:
        return "#d29922"
    if status:
        return "#f85149"
    return TEXT_SECONDARY


def _panel(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("PanelCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(6)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
    layout.addWidget(lbl)
    return frame, layout


class PrintersPage(QWidget):
    """Printers diagnostics page. Shows installed printers and pending print jobs."""

    fix_printer_requested = Signal(str)   # printer name

    def __init__(self) -> None:
        super().__init__()
        self._scanner = PrintersScanner(PowerShellRunner())
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("PanelCard")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("🖨 Printer Diagnostics")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)

        self._status_label = QLabel("Not scanned")
        self._status_label.setStyleSheet(secondary_text_style())
        h_layout.addWidget(self._status_label)
        h_layout.addSpacing(12)

        self._scan_btn = QPushButton("▶ Run Scan")
        self._scan_btn.clicked.connect(self._run_scan)
        h_layout.addWidget(self._scan_btn)

        outer.addWidget(header)

        # ── Scroll area ─────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._results_widget = QWidget()
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._results_layout.setSpacing(8)
        self._results_layout.setContentsMargins(0, 8, 0, 8)

        placeholder = QLabel("  Click '▶ Run Scan' to list installed printers.")
        placeholder.setStyleSheet(secondary_text_style() + " padding: 24px;")
        self._results_layout.addWidget(placeholder)

        scroll.setWidget(self._results_widget)
        outer.addWidget(scroll, stretch=1)

    def load_data(self, data: PrintersData, scanned_at: str = "") -> None:
        """Populate page with data from a shared Dashboard scan (no re-scan)."""
        self._display_results(data)
        ts = scanned_at[11:19] if len(scanned_at) >= 19 else ""
        self._status_label.setText(f"From Dashboard scan{f'  {ts}' if ts else ''}")
        self._status_label.setStyleSheet(secondary_text_style())

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setText("Scanning…")
        self._status_label.setStyleSheet("color: #d29922;")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        data = self._scanner.scan()
        self._display_results(data)

        self._scan_btn.setEnabled(True)
        self._status_label.setText(f"Done in {data.scan_duration_ms / 1000:.1f}s")
        self._status_label.setStyleSheet("color: #3fb950;")

    def _clear(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _display_results(self, data: PrintersData) -> None:
        self._clear()

        # ── Summary ──────────────────────────────────────────────────────────
        total = len(data.printers)
        ok = sum(1 for p in data.printers if p.status in _STATUS_OK)
        problem = total - ok
        jobs = len(data.print_jobs)

        frame, layout = _panel("Summary")
        row = QHBoxLayout()
        for text, color in [
            (f"✓ OK: {ok}", "#3fb950"),
            (f"⚠ Problem: {problem}", "#f85149" if problem > 0 else TEXT_SECONDARY),
            (f"🖨 Total: {total}", TEXT_SECONDARY),
            (f"📄 Print Jobs: {jobs}", "#d29922" if jobs > 0 else TEXT_SECONDARY),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; margin-right: 20px;")
            row.addWidget(lbl)
        row.addStretch(1)
        layout.addLayout(row)
        self._results_layout.addWidget(frame)

        # ── Printers list ────────────────────────────────────────────────────
        if data.printers:
            frame, layout = _panel(f"🖨 Installed Printers ({total})")
            for p in data.printers:
                prow = QHBoxLayout()
                prow.setSpacing(0)

                # Name + default badge
                name_txt = f"★ {p.name}" if p.is_default else p.name
                name_lbl = QLabel(name_txt)
                name_lbl.setFixedWidth(220)
                name_lbl.setStyleSheet(
                    "font-weight: bold; color: #d29922;" if p.is_default
                    else "font-weight: bold;"
                )
                prow.addWidget(name_lbl)

                # Type badge
                type_lbl = QLabel(p.printer_type or "—")
                type_lbl.setFixedWidth(90)
                type_lbl.setStyleSheet(secondary_text_style())
                prow.addWidget(type_lbl)

                # Status badge
                color = _status_color(p.status)
                icon = "✓" if p.status in _STATUS_OK else "✕"
                st_lbl = QLabel(f"{icon} {p.status or '—'}")
                st_lbl.setFixedWidth(130)
                st_lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
                prow.addWidget(st_lbl)

                # Jobs
                jobs_lbl = QLabel(f"{p.job_count} job(s)" if p.job_count else "No jobs")
                jobs_lbl.setFixedWidth(80)
                jobs_lbl.setStyleSheet(
                    "color: #d29922;" if p.job_count > 0 else secondary_text_style()
                )
                prow.addWidget(jobs_lbl)

                # Driver / port info
                detail_lbl = QLabel(f"{p.driver_name}  |  {p.port_name}")
                detail_lbl.setStyleSheet(secondary_text_style(size=11))
                prow.addWidget(detail_lbl, stretch=1)

                # Fix button for printers with problems
                has_problem = p.status not in _STATUS_OK or p.job_count > 0
                if has_problem:
                    fix_btn = QPushButton("🔧 Fix")
                    fix_btn.setFixedWidth(65)
                    fix_btn.setStyleSheet(
                        "QPushButton { background: #b45309; color: white; border-radius: 4px;"
                        " padding: 3px 8px; font-size: 11px; font-weight: bold; }"
                        "QPushButton:hover { background: #d97706; }"
                    )
                    fix_btn.setToolTip(f"Open Fix Printer scenario for: {p.name}")
                    name = p.name
                    fix_btn.clicked.connect(lambda _=False, n=name: self.fix_printer_requested.emit(n))
                    prow.addWidget(fix_btn)

                layout.addLayout(prow)

            self._results_layout.addWidget(frame)

        else:
            frame, layout = _panel("🖨 Installed Printers")
            spooler_err = any(
                "spooler" in e.lower() or "get-printer" in e.lower()
                for e in data.errors
            )
            if spooler_err:
                layout.addWidget(info_banner(
                    "Printer scan failed — Print Spooler service may not be running.",
                    hint="Go to Fix Center → Start Print Spooler to fix this.",
                    level="error",
                ))
            else:
                layout.addWidget(info_banner(
                    "No printers installed on this computer.",
                    hint="Connect a printer or install a driver to see it here.",
                    level="info",
                ))
            self._results_layout.addWidget(frame)

        # ── Print jobs (only if any) ─────────────────────────────────────────
        if data.print_jobs:
            frame, layout = _panel(f"📄 Active Print Jobs ({len(data.print_jobs)})")

            # Header row
            hdr = QHBoxLayout()
            for txt, w in [("ID", 40), ("Printer", 180), ("Document", 200), ("User", 100), ("Pages", 60), ("Status", 0)]:
                lbl = QLabel(txt)
                lbl.setStyleSheet(secondary_text_style(size=11))
                if w:
                    lbl.setFixedWidth(w)
                hdr.addWidget(lbl)
            hdr.addStretch(1)
            layout.addLayout(hdr)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setObjectName("SeparatorLine")
            layout.addWidget(sep)

            for j in data.print_jobs:
                jrow = QHBoxLayout()
                jrow.setSpacing(0)

                id_lbl = QLabel(str(j.job_id))
                id_lbl.setFixedWidth(40)
                jrow.addWidget(id_lbl)

                pr_lbl = QLabel(j.printer_name or "—")
                pr_lbl.setFixedWidth(180)
                pr_lbl.setStyleSheet(secondary_text_style())
                jrow.addWidget(pr_lbl)

                doc_lbl = QLabel(j.document_name or "—")
                doc_lbl.setFixedWidth(200)
                jrow.addWidget(doc_lbl)

                user_lbl = QLabel(j.user_name or "—")
                user_lbl.setFixedWidth(100)
                user_lbl.setStyleSheet(secondary_text_style())
                jrow.addWidget(user_lbl)

                pages_lbl = QLabel(str(j.total_pages) if j.total_pages is not None else "—")
                pages_lbl.setFixedWidth(60)
                pages_lbl.setStyleSheet(secondary_text_style())
                jrow.addWidget(pages_lbl)

                color = _job_color(j.status)
                st_lbl = QLabel(j.status or "—")
                st_lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
                jrow.addWidget(st_lbl, stretch=1)

                layout.addLayout(jrow)

            self._results_layout.addWidget(frame)

        # ── Errors ───────────────────────────────────────────────────────────
        if data.errors:
            frame, layout = _panel(f"⚠ Scan Warnings ({len(data.errors)})")
            for e in data.errors:
                layout.addWidget(info_banner(e, level="warning"))
            self._results_layout.addWidget(frame)

        self._results_layout.addStretch(1)
