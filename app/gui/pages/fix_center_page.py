"""Fix Center v1 — controlled execution of LOW/MEDIUM fixes with confirmation.

Architecture constraints (from docs/architecture_notes.md):
- No fix executes without explicit user confirmation.
- Every Apply goes through a confirmation QMessageBox.
- Admin check runs before any Apply — if not admin, Apply is disabled.
- Only LOW/MEDIUM fixes are in scope for v1 (no Danger Zone actions).
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner, is_admin, restart_as_admin
from app.core.risk_level import RiskLevel
from app.gui.styles import secondary_text_style
from app.gui.widgets.risk_badge import RiskBadge


# Context: agent_reports/2026-06-30_fix-center-v1.md
@dataclass(frozen=True)
class FixAction:
    id: str
    title: str
    description: str
    what_it_changes: str
    risk_level: RiskLevel
    requires_admin: bool
    ps_command: str
    check_cmd: str = ""


_AVAILABLE_FIXES: tuple[FixAction, ...] = (
    FixAction(
        id="SET_NETWORK_PRIVATE",
        title="Set Network Profile to Private",
        description=(
            "Changes all Public network profiles to Private. "
            "Public profile blocks file sharing, Network Discovery, and printer sharing by default."
        ),
        what_it_changes="Network profile category (Public → Private) on all active adapters",
        risk_level=RiskLevel.LOW,
        requires_admin=True,
        ps_command=(
            "Get-NetConnectionProfile | "
            "Where-Object {$_.NetworkCategory -eq 'Public'} | "
            "Set-NetConnectionProfile -NetworkCategory Private"
        ),
        check_cmd="(Get-NetConnectionProfile | Where {$_.NetworkCategory -eq 'Private'}).Count -gt 0",
    ),
    FixAction(
        id="ENABLE_NETWORK_DISCOVERY",
        title="Enable Network Discovery (Firewall)",
        description=(
            "Enables the 'Network Discovery' Windows Firewall rule group so this PC "
            "can find and be found by other devices on the local network."
        ),
        what_it_changes="Windows Defender Firewall — Network Discovery rule group (inbound/outbound)",
        risk_level=RiskLevel.LOW,
        requires_admin=True,
        ps_command='netsh advfirewall firewall set rule group="network discovery" new enable=Yes',
        check_cmd='(netsh advfirewall firewall show rule name="Network Discovery" | Select-String "Enabled:\\s+Yes").Count -gt 0',
    ),
    FixAction(
        id="ENABLE_FILE_PRINTER_SHARING",
        title="Enable File and Printer Sharing (Firewall)",
        description=(
            "Enables the 'File and Printer Sharing' Windows Firewall rule group, "
            "allowing access to shared folders and printers on this machine."
        ),
        what_it_changes="Windows Defender Firewall — File and Printer Sharing rule group (inbound/outbound)",
        risk_level=RiskLevel.LOW,
        requires_admin=True,
        ps_command='netsh advfirewall firewall set rule group="file and printer sharing" new enable=Yes',
        check_cmd='(netsh advfirewall firewall show rule name="File and Printer Sharing" | Select-String "Enabled:\\s+Yes").Count -gt 0',
    ),
    FixAction(
        id="START_PRINT_SPOOLER",
        title="Start Print Spooler Service",
        description=(
            "Starts the Print Spooler (Spooler) service and sets its startup type to Automatic. "
            "Required for printing to function."
        ),
        what_it_changes="Print Spooler service: state → Running, startup → Automatic",
        risk_level=RiskLevel.LOW,
        requires_admin=True,
        ps_command="Start-Service Spooler -ErrorAction Stop; Set-Service Spooler -StartupType Automatic",
        check_cmd="(Get-Service Spooler).Status -eq 'Running'",
    ),
    FixAction(
        id="START_FDRESPUB",
        title="Start FDResPub Service (Network Discovery)",
        description=(
            "Starts the Function Discovery Resource Publication (FDResPub) service, "
            "making this PC visible to other devices in Windows Network Discovery."
        ),
        what_it_changes="FDResPub service: state → Running",
        risk_level=RiskLevel.LOW,
        requires_admin=True,
        ps_command="Start-Service FDResPub -ErrorAction Stop",
        check_cmd="(Get-Service FDResPub).Status -eq 'Running'",
    ),
)


class _FixActionCard(QFrame):
    """One fix action row: description + Apply/Skip buttons."""

    def __init__(self, action: FixAction, runner: PowerShellRunner, is_admin: bool) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        self._action = action
        self._runner = runner
        self._is_admin = is_admin

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel(f"⚙ {action.title}")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        title_row.addWidget(title_lbl)
        title_row.addStretch(1)
        title_row.addWidget(RiskBadge(str(action.risk_level)))
        outer.addLayout(title_row)

        # Description
        desc = QLabel(action.description)
        desc.setWordWrap(True)
        outer.addWidget(desc)

        # Metadata
        meta_row = QHBoxLayout()
        meta_row.addWidget(_muted("What changes:"))
        changes_lbl = QLabel(action.what_it_changes)
        changes_lbl.setStyleSheet(secondary_text_style(size=11))
        meta_row.addWidget(changes_lbl)
        meta_row.addStretch(1)
        if action.requires_admin:
            admin_lbl = QLabel("⚠ Requires admin")
            admin_lbl.setStyleSheet("color: #d29922; font-size: 11px;")
            meta_row.addWidget(admin_lbl)
        outer.addLayout(meta_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #30363d;")
        outer.addWidget(sep)

        # Action row
        action_row = QHBoxLayout()
        self._result_label = QLabel("")
        self._result_label.setStyleSheet("font-size: 11px;")
        self._result_label.hide()
        action_row.addWidget(self._result_label)
        action_row.addStretch(1)

        self._skip_btn = QPushButton("Skip")
        self._skip_btn.setFixedWidth(72)
        self._skip_btn.clicked.connect(self._on_skip)
        action_row.addWidget(self._skip_btn)

        can_apply = is_admin or not action.requires_admin
        self._apply_btn = QPushButton("▶ Apply Fix")
        self._apply_btn.setFixedWidth(110)
        if can_apply:
            self._apply_btn.clicked.connect(self._on_apply)
            self._apply_btn.setStyleSheet(
                "QPushButton { background: #238636; color: white; border-radius: 4px; padding: 4px 10px; }"
                "QPushButton:hover { background: #2ea043; }"
                "QPushButton:disabled { background: #E5E7EB; color: #4B5563; }"
            )
        else:
            self._apply_btn.setEnabled(False)
            self._apply_btn.setToolTip("Restart app as Administrator to apply fixes.")
            self._apply_btn.setStyleSheet(
                "QPushButton { background: #E5E7EB; color: #4B5563; border-radius: 4px; padding: 4px 10px; }"
            )
        action_row.addWidget(self._apply_btn)
        outer.addLayout(action_row)
        self._apply_current_status()

    # Context: agent_reports/2026-07-01_fix-status-summary-report-client-summary.md
    def _apply_current_status(self) -> None:
        if not self._action.check_cmd:
            return
        result = self._runner.run(self._action.check_cmd, timeout=10)
        is_active = result.succeeded and result.stdout.strip().lower() == "true"
        if not is_active:
            return
        self._result_label.setText("✓ Already active")
        self._result_label.setStyleSheet("font-size: 11px; color: #3fb950; font-weight: bold;")
        self._result_label.show()
        self._apply_btn.hide()

    def _on_skip(self) -> None:
        self._result_label.setText("⊘ Skipped")
        self._result_label.setStyleSheet(secondary_text_style(size=11))
        self._result_label.show()
        self._apply_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)

    def _on_apply(self) -> None:
        a = self._action
        confirmed = QMessageBox.question(
            self,
            "Confirm action",
            f"<b>{a.title}</b><br><br>"
            f"What changes: <i>{a.what_it_changes}</i><br><br>"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return

        self._apply_btn.setEnabled(False)
        self._apply_btn.setText("Applying…")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        result = self._runner.run(a.ps_command, timeout=20)

        if result.succeeded:
            self._result_label.setText("✓ Successfully applied")
            self._result_label.setStyleSheet("font-size: 11px; color: #3fb950; font-weight: bold;")
            self._skip_btn.setEnabled(False)
            self._apply_btn.setText("✓ Applied")
            self._apply_btn.setStyleSheet(
                "QPushButton { background: #1a4731; color: #3fb950; border-radius: 4px; padding: 4px 10px; }"
            )
        else:
            err = (result.stderr or "Unknown error").strip()[:160]
            self._result_label.setText(f"✕ Error: {err}")
            self._result_label.setStyleSheet("font-size: 11px; color: #f85149;")
            self._apply_btn.setEnabled(True)
            self._apply_btn.setText("▶ Retry")

        self._result_label.show()


def _muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(secondary_text_style(size=11))
    return lbl


class FixCenterPage(QWidget):
    """Fix Center — lists available LOW/MEDIUM fixes; each requires explicit confirmation."""

    def __init__(self) -> None:
        super().__init__()
        self._runner = PowerShellRunner()
        self._is_admin = is_admin()
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("PanelCard")
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(16, 10, 16, 10)

        title = QLabel("🔧 Fix Center")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_row.addWidget(title)
        h_row.addStretch(1)

        if self._is_admin:
            admin_badge = QLabel("✓ Administrator")
            admin_badge.setStyleSheet(
                "background: #238636; color: white; border-radius: 4px; "
                "padding: 2px 10px; font-weight: bold;"
            )
        else:
            admin_badge = QLabel("⚠ Standard user")
            admin_badge.setStyleSheet(
                "background: #b45309; color: white; border-radius: 4px; "
                "padding: 2px 10px; font-weight: bold;"
            )
        h_row.addWidget(admin_badge)
        outer.addWidget(header)

        # ── Admin elevation banner (if not admin) ────────────────────────────
        if not self._is_admin:
            banner = QFrame()
            banner.setStyleSheet(
                "QFrame { background: #2d2209; border-left: 3px solid #d29922; margin: 0; }"
            )
            b_layout = QHBoxLayout(banner)
            b_layout.setContentsMargins(16, 10, 16, 10)
            b_layout.setSpacing(12)

            b_msg = QLabel(
                "⚠  Running without administrator privileges — Apply buttons are disabled."
            )
            b_msg.setStyleSheet("color: #d29922;")
            b_msg.setWordWrap(True)
            b_layout.addWidget(b_msg, stretch=1)

            restart_btn = QPushButton("🛡  Restart as Administrator")
            restart_btn.setFixedWidth(210)
            restart_btn.setStyleSheet(
                "QPushButton { background: #b45309; color: white; border: none;"
                " border-radius: 5px; padding: 6px 14px; font-weight: 600; }"
                "QPushButton:hover { background: #d97706; }"
            )
            restart_btn.setToolTip(
                "Zatvori aplikaciju i ponovo pokreni sa administratorskim privilegijama (UAC prompt)."
            )
            restart_btn.clicked.connect(restart_as_admin)
            b_layout.addWidget(restart_btn)

            outer.addWidget(banner)

        # ── Scrollable action list ──────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        for action in _AVAILABLE_FIXES:
            content_layout.addWidget(
                _FixActionCard(action, self._runner, self._is_admin)
            )

        content_layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)
