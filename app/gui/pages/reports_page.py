from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.modules.network.scanner import NetworkScanner
from app.modules.printers.scanner import PrintersScanner
from app.modules.services.scanner import ServicesScanner
from app.modules.smb.scanner import SmbScanner
from app.reports.html_report import write_html
from app.reports.json_report import write_json
from app.reports.markdown_report import write_markdown
from app.reports.models import ScanReport

_FORMAT_EXT = {"JSON": ".json", "Markdown": ".md", "HTML": ".html"}


class ReportsPage(QWidget):
    """Scan all selected modules and export a diagnostic report (JSON / Markdown / HTML)."""

    def __init__(self) -> None:
        super().__init__()
        self._runner = PowerShellRunner()
        self._last_report: str = ""
        self._last_ext: str = ".txt"
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

        title = QLabel("📊 Report Generator")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #9aa4b2;")
        h_layout.addWidget(self._status_label)

        outer.addWidget(header)

        # ── Options panel ───────────────────────────────────────────────────
        opts_frame = QFrame()
        opts_frame.setObjectName("PanelCard")
        opts_layout = QHBoxLayout(opts_frame)
        opts_layout.setContentsMargins(16, 12, 16, 12)
        opts_layout.setSpacing(32)

        # Sections
        sections_col = QVBoxLayout()
        sections_col.addWidget(QLabel("Include sections:"))
        sections_col.setSpacing(4)
        self._cb_network = QCheckBox("Network")
        self._cb_network.setChecked(True)
        self._cb_smb = QCheckBox("SMB / File Sharing")
        self._cb_smb.setChecked(True)
        self._cb_services = QCheckBox("Services")
        self._cb_services.setChecked(True)
        self._cb_printers = QCheckBox("Printers")
        self._cb_printers.setChecked(True)
        for cb in (self._cb_network, self._cb_smb, self._cb_services, self._cb_printers):
            sections_col.addWidget(cb)
        opts_layout.addLayout(sections_col)

        # SMB target IP (shown always, used only when SMB checked)
        ip_col = QVBoxLayout()
        ip_col.setSpacing(4)
        ip_col.addWidget(QLabel("SMB target IP (optional):"))
        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g. 192.168.1.50")
        self._ip_input.setMaximumWidth(200)
        ip_col.addWidget(self._ip_input)
        ip_col.addStretch(1)
        opts_layout.addLayout(ip_col)

        # Format
        fmt_col = QVBoxLayout()
        fmt_col.setSpacing(4)
        fmt_col.addWidget(QLabel("Output format:"))
        self._rb_json = QRadioButton("JSON")
        self._rb_md = QRadioButton("Markdown")
        self._rb_html = QRadioButton("HTML")
        self._rb_md.setChecked(True)
        for rb in (self._rb_json, self._rb_md, self._rb_html):
            fmt_col.addWidget(rb)
        opts_layout.addLayout(fmt_col)

        opts_layout.addStretch(1)

        # Action buttons
        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        self._gen_btn = QPushButton("▶ Generate & Preview")
        self._gen_btn.clicked.connect(self._generate)
        btn_col.addWidget(self._gen_btn)

        self._save_btn = QPushButton("💾 Save to File")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_file)
        btn_col.addWidget(self._save_btn)
        btn_col.addStretch(1)
        opts_layout.addLayout(btn_col)

        outer.addWidget(opts_frame)

        # ── Preview area ────────────────────────────────────────────────────
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFont(_monospace_font())
        self._preview.setPlaceholderText("Report preview will appear here after generation.")
        self._preview.setStyleSheet(
            "QPlainTextEdit { background: #0d1117; color: #c9d1d9; "
            "border: none; font-size: 12px; padding: 12px; }"
        )
        outer.addWidget(self._preview, stretch=1)

    # ── Actions ─────────────────────────────────────────────────────────────

    def _generate(self) -> None:
        self._gen_btn.setEnabled(False)
        self._save_btn.setEnabled(False)
        self._preview.setPlainText("")
        self._status_label.setText("Scanning…")
        self._status_label.setStyleSheet("color: #d29922;")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        report = self._build_report()
        text = self._render(report)

        self._last_report = text
        self._last_ext = _FORMAT_EXT[self._selected_format()]
        self._preview.setPlainText(text)

        self._gen_btn.setEnabled(True)
        self._save_btn.setEnabled(True)
        self._status_label.setText("Generated")
        self._status_label.setStyleSheet("color: #3fb950;")

    def _build_report(self) -> ScanReport:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        target_ip = self._ip_input.text().strip()

        network = None
        smb = None
        services = None
        printers = None

        if self._cb_network.isChecked():
            self._status_label.setText("Scanning Network…")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            network = NetworkScanner(self._runner).scan()

        if self._cb_smb.isChecked():
            self._status_label.setText("Scanning SMB…")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            smb = SmbScanner(self._runner).scan(target_ip=target_ip)

        if self._cb_services.isChecked():
            self._status_label.setText("Scanning Services…")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            services = ServicesScanner(self._runner).scan()

        if self._cb_printers.isChecked():
            self._status_label.setText("Scanning Printers…")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            printers = PrintersScanner(self._runner).scan()

        hostname = network.hostname if network else ""
        return ScanReport(
            generated_at=ts,
            hostname=hostname,
            network=network,
            smb=smb,
            smb_target_ip=target_ip,
            services=services,
            printers=printers,
        )

    def _render(self, report: ScanReport) -> str:
        from app.core.decision_engine import DecisionEngine
        issues = DecisionEngine().analyze(report)

        fmt = self._selected_format()
        if fmt == "JSON":
            return write_json(report, issues)
        if fmt == "HTML":
            return write_html(report, issues)
        return write_markdown(report, issues)

    def _save_file(self) -> None:
        fmt = self._selected_format()
        ext = self._last_ext
        default_name = f"fieldfix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"

        filters = {
            "JSON": "JSON Files (*.json)",
            "Markdown": "Markdown Files (*.md)",
            "HTML": "HTML Files (*.html)",
        }
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", default_name, filters[fmt]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._last_report)
            self._status_label.setText(f"Saved: {os.path.basename(path)}")
            self._status_label.setStyleSheet("color: #3fb950;")
        except OSError as exc:
            self._status_label.setText(f"Save failed: {exc}")
            self._status_label.setStyleSheet("color: #f85149;")

    def _selected_format(self) -> str:
        if self._rb_json.isChecked():
            return "JSON"
        if self._rb_html.isChecked():
            return "HTML"
        return "Markdown"


def _monospace_font():
    from PySide6.QtGui import QFont
    font = QFont("Consolas")
    font.setPointSize(10)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font
