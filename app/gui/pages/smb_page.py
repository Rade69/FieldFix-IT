from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.modules.smb.models import SmbData
from app.modules.smb.scanner import NET_VIEW_ERROR_HINTS, SmbScanner


def _bool_badge(value: bool | None, true_text: str = "Yes", false_text: str = "No") -> QLabel:
    if value is None:
        label = QLabel("—")
        label.setStyleSheet("color: #9aa4b2;")
    elif value:
        label = QLabel(f"✓ {true_text}")
        label.setStyleSheet("color: #3fb950; font-weight: bold;")
    else:
        label = QLabel(f"✕ {false_text}")
        label.setStyleSheet("color: #f85149; font-weight: bold;")
    return label


def _kv_row(key: str, value_widget: QWidget | None = None, value_str: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    key_label = QLabel(key)
    key_label.setStyleSheet("color: #9aa4b2; min-width: 240px;")
    key_label.setAlignment(Qt.AlignmentFlag.AlignTop)
    row.addWidget(key_label)
    if value_widget:
        row.addWidget(value_widget, stretch=1)
    else:
        v = QLabel(value_str)
        v.setStyleSheet("font-weight: bold;")
        v.setWordWrap(True)
        row.addWidget(v, stretch=1)
    return row


def _panel(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("PanelCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(6)
    t = QLabel(title)
    t.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
    layout.addWidget(t)
    return frame, layout


class SmbPage(QWidget):
    """SMB / Sharing diagnostics page. Optional target IP enables port check + net view."""

    def __init__(self) -> None:
        super().__init__()
        self._scanner = SmbScanner(PowerShellRunner())
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

        title = QLabel("📂 SMB / Sharing Diagnostics")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)

        ip_label = QLabel("Target IP:")
        ip_label.setStyleSheet("color: #9aa4b2;")
        h_layout.addWidget(ip_label)
        h_layout.addSpacing(4)

        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g. 192.168.1.100  (optional)")
        self._ip_input.setFixedWidth(220)
        h_layout.addWidget(self._ip_input)
        h_layout.addSpacing(12)

        self._status_label = QLabel("Not scanned")
        self._status_label.setStyleSheet("color: #9aa4b2;")
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

        placeholder = QLabel("  Click '▶ Run Scan' to collect SMB information.")
        placeholder.setStyleSheet("color: #9aa4b2; padding: 24px;")
        self._results_layout.addWidget(placeholder)

        scroll.setWidget(self._results_widget)
        outer.addWidget(scroll, stretch=1)

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setText("Scanning…")
        self._status_label.setStyleSheet("color: #d29922;")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        target_ip = self._ip_input.text().strip()
        data = self._scanner.scan(target_ip=target_ip)
        self._display_results(data)

        self._scan_btn.setEnabled(True)
        self._status_label.setText(f"Done in {data.scan_duration_ms / 1000:.1f}s")
        self._status_label.setStyleSheet("color: #3fb950;")

    def _clear(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _display_results(self, data: SmbData) -> None:
        self._clear()

        # ── SMB Server Config ───────────────────────────────────────────────
        frame, layout = _panel("🖥 SMB Server Configuration")
        if data.server_config:
            sc = data.server_config
            layout.addLayout(_kv_row("SMB1 Enabled", _bool_badge(sc.smb1_enabled, "Enabled (⚠ risk)", "Disabled (safe)")))
            layout.addLayout(_kv_row("SMB2 Enabled", _bool_badge(sc.smb2_enabled, "Enabled", "Disabled")))
            layout.addLayout(_kv_row("Security Signature Required", _bool_badge(sc.require_security_signature)))
            layout.addLayout(_kv_row("Security Signature Enabled", _bool_badge(sc.enable_security_signature)))
        else:
            layout.addWidget(QLabel("  Not available (Get-SmbServerConfiguration failed)"))
        self._results_layout.addWidget(frame)

        # ── SMB Client Config ───────────────────────────────────────────────
        frame, layout = _panel("💻 SMB Client Configuration")
        if data.client_config:
            cc = data.client_config
            layout.addLayout(_kv_row(
                "Insecure Guest Logons",
                _bool_badge(cc.enable_insecure_guest_logons,
                            true_text="Allowed (⚠ risk)", false_text="Blocked (secure)"),
            ))
            layout.addLayout(_kv_row("Security Signature Required", _bool_badge(cc.require_security_signature)))
            layout.addLayout(_kv_row("Security Signature Enabled", _bool_badge(cc.enable_security_signature)))
        else:
            layout.addWidget(QLabel("  Not available (Get-SmbClientConfiguration failed)"))
        self._results_layout.addWidget(frame)

        # ── Local Shares ────────────────────────────────────────────────────
        frame, layout = _panel(f"📁 Local Shares ({len(data.shares)})")
        if data.shares:
            for s in data.shares:
                desc = f"{s.path or '—'}  [{s.share_type}]"
                if s.description:
                    desc += f"  — {s.description}"
                layout.addLayout(_kv_row(s.name, value_str=desc))
        else:
            layout.addWidget(QLabel("  No shares found or scan failed."))
        self._results_layout.addWidget(frame)

        # ── Port 445 ────────────────────────────────────────────────────────
        if data.port_445 is not None:
            pr = data.port_445
            frame, layout = _panel(f"🔌 Port 445 — {pr.target_ip}")
            if pr.reachable is True:
                badge = QLabel("✓ Open")
                badge.setStyleSheet("color: #3fb950; font-weight: bold;")
            elif pr.reachable is False:
                badge = QLabel("✕ Closed / Filtered")
                badge.setStyleSheet("color: #f85149; font-weight: bold;")
            else:
                badge = QLabel("— Check failed")
                badge.setStyleSheet("color: #9aa4b2;")
            layout.addLayout(_kv_row("TCP 445", badge))
            self._results_layout.addWidget(frame)

        # ── Net View ────────────────────────────────────────────────────────
        if data.net_view_success is not None:
            ip = self._ip_input.text().strip()
            frame, layout = _panel(f"🔍 net view \\\\{ip}")
            if data.net_view_success:
                if data.net_view_entries:
                    for e in data.net_view_entries:
                        layout.addLayout(_kv_row(e.name, value_str=f"{e.share_type}  {e.comment}".strip()))
                else:
                    layout.addWidget(QLabel("  No shares visible."))
            else:
                code = data.net_view_error_code
                hint = NET_VIEW_ERROR_HINTS.get(code, "") if code else ""
                err_label = QLabel(f"✕ Error {code}" if code else "✕ Failed")
                err_label.setStyleSheet("color: #f85149; font-weight: bold;")
                layout.addLayout(_kv_row("Result", err_label))
                if hint:
                    hint_label = QLabel(hint)
                    hint_label.setStyleSheet("color: #d29922;")
                    hint_label.setWordWrap(True)
                    layout.addWidget(hint_label)
            self._results_layout.addWidget(frame)

        # ── Errors ──────────────────────────────────────────────────────────
        if data.errors:
            frame, layout = _panel(f"⚠ Scan Warnings ({len(data.errors)})")
            for i, e in enumerate(data.errors, 1):
                layout.addLayout(_kv_row(f"#{i}", value_str=e))
            self._results_layout.addWidget(frame)

        self._results_layout.addStretch(1)
