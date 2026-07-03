from PySide6.QtCore import Qt
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
from app.modules.services.models import ServicesData
from app.modules.services.scanner import ServicesScanner

_STATUS_COLOR = {
    "Running":       "#3fb950",
    "Stopped":       "#f85149",
    "StartPending":  "#d29922",
    "StopPending":   "#d29922",
    "Paused":        "#d29922",
    "NotFound":      TEXT_SECONDARY,
}

_START_TYPE_COLOR = {
    "Automatic":     "#3fb950",
    "Manual":        TEXT_SECONDARY,
    "Disabled":      "#f85149",
}


def _status_label(status: str) -> QLabel:
    color = _STATUS_COLOR.get(status, TEXT_SECONDARY)
    icon = "✓" if status == "Running" else ("✕" if status == "Stopped" else "●")
    label = QLabel(f"{icon} {status}")
    label.setStyleSheet(f"color: {color}; font-weight: bold;")
    return label


class ServicesPage(QWidget):
    """Windows Services diagnostics page. Shows status of networking/print services."""

    def __init__(self) -> None:
        super().__init__()
        self._scanner = ServicesScanner(PowerShellRunner())
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

        title = QLabel("⚙ Services Diagnostics")
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

        placeholder = QLabel("  Click '▶ Run Scan' to check Windows service states.")
        placeholder.setStyleSheet(secondary_text_style() + " padding: 24px;")
        self._results_layout.addWidget(placeholder)

        scroll.setWidget(self._results_widget)
        outer.addWidget(scroll, stretch=1)

    def load_data(self, data: ServicesData, scanned_at: str = "") -> None:
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

    def _display_results(self, data: ServicesData) -> None:
        self._clear()

        # ── Summary badges ──────────────────────────────────────────────────
        running = sum(1 for s in data.services if s.status == "Running")
        stopped = sum(1 for s in data.services if s.status == "Stopped")
        total = len(data.services)

        summary_frame = QFrame()
        summary_frame.setObjectName("PanelCard")
        s_layout = QHBoxLayout(summary_frame)
        s_layout.setContentsMargins(16, 10, 16, 10)

        for text, color in [
            (f"✓ Running: {running}", "#3fb950"),
            (f"✕ Stopped: {stopped}", "#f85149" if stopped > 0 else TEXT_SECONDARY),
            (f"Total monitored: {total}", TEXT_SECONDARY),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; margin-right: 24px;")
            s_layout.addWidget(lbl)
        s_layout.addStretch(1)
        self._results_layout.addWidget(summary_frame)

        # ── Services table ──────────────────────────────────────────────────
        table_frame = QFrame()
        table_frame.setObjectName("PanelCard")
        t_layout = QVBoxLayout(table_frame)
        t_layout.setContentsMargins(16, 12, 16, 12)
        t_layout.setSpacing(10)

        # Header row
        hdr = QHBoxLayout()
        for txt, w in [("Service", 180), ("Display Name", 220), ("Status", 120), ("Startup", 100), ("Potrebno za", 0)]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(secondary_text_style(size=11))
            if w:
                lbl.setFixedWidth(w)
            hdr.addWidget(lbl)
        hdr.addStretch(1)
        t_layout.addLayout(hdr)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("SeparatorLine")
        t_layout.addWidget(sep)

        # Service rows
        for svc in data.services:
            row = QHBoxLayout()
            row.setSpacing(0)

            name_lbl = QLabel(svc.name)
            name_lbl.setFixedWidth(180)
            name_lbl.setStyleSheet("font-weight: bold;")
            row.addWidget(name_lbl)

            display_lbl = QLabel(svc.display_name or "—")
            display_lbl.setFixedWidth(220)
            display_lbl.setStyleSheet(secondary_text_style())
            row.addWidget(display_lbl)

            row.addWidget(_status_label(svc.status))
            # Stretch spacer between status and startup
            spacer = QWidget()
            spacer.setFixedWidth(120 - 90)
            row.addWidget(spacer)

            st_color = _START_TYPE_COLOR.get(svc.start_type, TEXT_SECONDARY)
            st_lbl = QLabel(svc.start_type or "—")
            st_lbl.setFixedWidth(100)
            st_lbl.setStyleSheet(f"color: {st_color};")
            row.addWidget(st_lbl)

            req_lbl = QLabel(svc.required_for)
            req_lbl.setStyleSheet(secondary_text_style(size=11))
            req_lbl.setWordWrap(True)
            row.addWidget(req_lbl, stretch=1)

            t_layout.addLayout(row)

        self._results_layout.addWidget(table_frame)

        # ── Errors ──────────────────────────────────────────────────────────
        if data.errors:
            err_frame = QFrame()
            err_frame.setObjectName("PanelCard")
            e_layout = QVBoxLayout(err_frame)
            e_layout.setContentsMargins(16, 12, 16, 12)
            title = QLabel(f"⚠ Warnings ({len(data.errors)})")
            title.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
            e_layout.addWidget(title)
            for e in data.errors:
                lbl = QLabel(e)
                lbl.setStyleSheet("color: #d29922;")
                lbl.setWordWrap(True)
                e_layout.addWidget(lbl)
            self._results_layout.addWidget(err_frame)

        self._results_layout.addStretch(1)
