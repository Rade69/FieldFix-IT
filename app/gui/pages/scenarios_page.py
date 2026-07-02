"""Scenarios page — guided diagnostic workflows.

Each scenario runs a targeted scan and presents results as a
pass/fail checklist with direct links to Fix Center actions.
"""

from __future__ import annotations

import ipaddress

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner, is_admin, restart_as_admin
from app.core.scan_session import ScanResult, ScanSession
from app.core.scenario import ALL_SCENARIOS, CheckItem, RemoteStep, Scenario, run_checks, run_remote_checklist
from app.modules.network.models import DiscoveredDevice
from app.modules.network.subnet_scanner import SubnetScanner


def _is_valid_ipv4(ip: str) -> bool:
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
        return False


# ── Background worker — scan ──────────────────────────────────────────────────

class _ScenarioWorker(QThread):
    progress = Signal(str)
    finished = Signal(object)   # ScanResult

    def __init__(self, runner: PowerShellRunner, target_ip: str) -> None:
        super().__init__()
        self._runner = runner
        self._target_ip = target_ip

    def run(self) -> None:
        result = ScanSession(self._runner).run(
            smb_target_ip=self._target_ip,
            on_progress=self.progress.emit,
        )
        self.finished.emit(result)


# ── Background worker — printer install ──────────────────────────────────────

class _PrinterInstallWorker(QThread):
    finished = Signal(bool, str)   # success, message

    def __init__(self, runner: PowerShellRunner, ip: str) -> None:
        super().__init__()
        self._runner = runner
        self._ip = ip

    def run(self) -> None:
        ip = self._ip
        port_name = f"IP_{ip}"
        printer_name = f"Network Printer ({ip})"
        ps = (
            f"$ip = '{ip}'\n"
            f"$portName = '{port_name}'\n"
            f"$printerName = '{printer_name}'\n"
            # Ensure TCP/IP port exists
            "if (-not (Get-PrinterPort -Name $portName -ErrorAction SilentlyContinue)) {\n"
            "    Add-PrinterPort -Name $portName -PrinterHostAddress $ip -ErrorAction Stop\n"
            "}\n"
            # OEM drivers first (anything not Microsoft/Generic/Remote/Fax)
            "$oem = Get-PrinterDriver -ErrorAction SilentlyContinue |\n"
            "    Where-Object { $_.Name -notmatch 'Microsoft|Generic|Remote|Fax|OneNote|XPS|PDF' } |\n"
            "    Select-Object -ExpandProperty Name\n"
            "$fallback = @('Microsoft IPP Class Driver', 'Generic / Text Only')\n"
            "$drvList = if ($oem) { @($oem) + $fallback } else { $fallback }\n"
            "foreach ($drv in $drvList) {\n"
            "    if (-not (Get-PrinterDriver -Name $drv -ErrorAction SilentlyContinue)) { continue }\n"
            # If printer already exists: update its driver instead of re-adding
            "    $existing = Get-Printer -Name $printerName -ErrorAction SilentlyContinue\n"
            "    if ($existing) {\n"
            "        if ($existing.DriverName -eq $drv) {\n"
            "            Write-Output \"OK:$drv (already up to date)\"\n"
            "        } else {\n"
            "            Set-Printer -Name $printerName -DriverName $drv -ErrorAction Stop\n"
            "            Write-Output \"OK:$drv (driver updated)\"\n"
            "        }\n"
            "    } else {\n"
            "        Add-Printer -Name $printerName -DriverName $drv -PortName $portName -ErrorAction Stop\n"
            "        Write-Output \"OK:$drv\"\n"
            "    }\n"
            "    exit\n"
            "}\n"
            "throw 'No compatible driver found. Install the manufacturer driver and click Install again.'"
        )
        result = self._runner.run(ps, timeout=60)
        if result.succeeded and "OK:" in result.stdout:
            driver = result.stdout.split("OK:")[1].strip()
            self.finished.emit(True, f"Installed using: {driver}")
        else:
            err = (result.stderr or result.stdout or "Unknown error").strip()[:240]
            self.finished.emit(False, err)


# ── Background worker — printer network discovery ─────────────────────────────

class _PrinterDiscoveryWorker(QThread):
    progress = Signal(str)
    finished = Signal(list)   # list[DiscoveredDevice]

    def __init__(self, runner: PowerShellRunner) -> None:
        super().__init__()
        self._runner = runner

    def run(self) -> None:
        devices = SubnetScanner(self._runner).scan(on_progress=self.progress.emit)
        printers = [d for d in devices if d.device_type == "printer"]
        self.finished.emit(printers)


# ── Discovered printer card ───────────────────────────────────────────────────

class _PrinterDiscoveryPanel(QFrame):
    """Scans the local subnet for printers and lets user select one."""

    printer_selected = Signal(str, str)   # ip, display_name

    def __init__(self, runner: PowerShellRunner) -> None:
        super().__init__()
        self._runner = runner
        self._worker: _PrinterDiscoveryWorker | None = None

        self.setObjectName("PanelCard")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 14)
        outer.setSpacing(10)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("🔍 Find printers on this network")
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f0f6fc;")
        hdr.addWidget(title)
        hdr.addStretch(1)
        self._scan_btn = QPushButton("Scan network")
        self._scan_btn.setFixedWidth(110)
        self._scan_btn.setStyleSheet(
            "QPushButton { background: #21262d; color: #58a6ff; border: 1px solid #30363d;"
            " border-radius: 4px; padding: 4px 10px; font-size: 11px; }"
            "QPushButton:hover { background: #30363d; }"
            "QPushButton:disabled { color: #6e7681; }"
        )
        self._scan_btn.clicked.connect(self.start_scan)
        hdr.addWidget(self._scan_btn)
        outer.addLayout(hdr)

        self._status_lbl = QLabel("Click 'Scan network' to discover printers on the local subnet.")
        self._status_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        outer.addWidget(self._status_lbl)

        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(6)
        outer.addLayout(self._cards_layout)

    def start_scan(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._scan_btn.setEnabled(False)
        self._scan_btn.setText("Scanning…")
        self._status_lbl.setText("Scanning subnet — this takes 5–10 seconds…")
        self._clear_cards()

        self._worker = _PrinterDiscoveryWorker(self._runner)
        self._worker.progress.connect(self._status_lbl.setText)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, printers: list) -> None:
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("Scan again")
        self._clear_cards()

        if not printers:
            self._status_lbl.setText(
                "No printers found. Make sure the printer is on and check Topology page."
            )
            return

        self._status_lbl.setText(
            f"Found {len(printers)} printer(s) — click to use:"
        )
        for dev in printers:
            self._add_printer_card(dev)

    def _add_printer_card(self, dev: DiscoveredDevice) -> None:
        name = dev.hostname or f"Printer at {dev.ip_address}"
        row = QFrame()
        row.setStyleSheet(
            "QFrame { background: #161b22; border: 1px solid #30363d;"
            " border-radius: 4px; }"
        )
        rl = QHBoxLayout(row)
        rl.setContentsMargins(12, 8, 12, 8)

        icon = QLabel("🖨")
        icon.setStyleSheet("font-size: 20px;")
        rl.addWidget(icon)

        info = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #f0f6fc;")
        ip_lbl = QLabel(dev.ip_address)
        ip_lbl.setStyleSheet("font-size: 11px; color: #58a6ff;")
        info.addWidget(name_lbl)
        info.addWidget(ip_lbl)
        rl.addLayout(info, stretch=1)

        use_btn = QPushButton("Use this printer")
        use_btn.setFixedWidth(130)
        use_btn.setStyleSheet(
            "QPushButton { background: #1f6feb; color: white; border-radius: 4px;"
            " padding: 4px 10px; font-size: 11px; }"
            "QPushButton:hover { background: #388bfd; }"
        )
        ip = dev.ip_address
        display = name
        use_btn.clicked.connect(lambda: self.printer_selected.emit(ip, display))
        rl.addWidget(use_btn)

        self._cards_layout.addWidget(row)

    def _clear_cards(self) -> None:
        while self._cards_layout.count():
            child = self._cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


# ── Scenario card (top selector) ──────────────────────────────────────────────

class _ScenarioCard(QFrame):
    selected = Signal(object)   # Scenario

    def __init__(self, scenario: Scenario) -> None:
        super().__init__()
        self._scenario = scenario
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("PanelCard")
        self.setFixedHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)

        icon = QLabel(scenario.icon)
        icon.setStyleSheet("font-size: 28px;")
        lay.addWidget(icon)

        text = QVBoxLayout()
        title = QLabel(scenario.title)
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #f0f6fc;")
        desc = QLabel(scenario.description.split("\n")[0])
        desc.setStyleSheet("color: #8b949e; font-size: 11px;")
        text.addWidget(title)
        text.addWidget(desc)
        lay.addLayout(text, stretch=1)

    def mousePressEvent(self, _event) -> None:
        self.selected.emit(self._scenario)

    def set_active(self, active: bool) -> None:
        self.setStyleSheet(
            "QFrame#PanelCard { border: 1px solid #58a6ff; background: #161b22; }"
            if active else ""
        )


# ── Single check row ──────────────────────────────────────────────────────────

class _CheckRow(QWidget):
    go_to_fix = Signal(str)     # fix_id

    def __init__(self, item: CheckItem) -> None:
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(10)

        icon = QLabel("✓" if item.passed else "✗")
        icon.setFixedWidth(18)
        icon.setStyleSheet(
            "color: #3fb950; font-weight: bold; font-size: 14px;"
            if item.passed else
            "color: #f85149; font-weight: bold; font-size: 14px;"
        )
        row.addWidget(icon)

        col = QVBoxLayout()
        col.setSpacing(2)

        label = QLabel(item.label)
        label.setStyleSheet("font-size: 12px; color: #c9d1d9;")
        col.addWidget(label)

        if not item.passed and item.detail:
            detail = QLabel(item.detail)
            detail.setStyleSheet("font-size: 11px; color: #8b949e;")
            detail.setWordWrap(True)
            col.addWidget(detail)

        row.addLayout(col, stretch=1)

        if not item.passed and item.fix_id:
            fix_btn = QPushButton("→ Fix Center")
            fix_btn.setFixedWidth(100)
            fix_btn.setStyleSheet(
                "QPushButton { background: #21262d; color: #58a6ff; border: 1px solid #30363d;"
                " border-radius: 4px; padding: 3px 8px; font-size: 11px; }"
                "QPushButton:hover { background: #30363d; }"
            )
            fix_btn.clicked.connect(lambda: self.go_to_fix.emit(item.fix_id))
            row.addWidget(fix_btn)


# ── Results panel ─────────────────────────────────────────────────────────────

class _ResultsPanel(QWidget):
    go_to_fix = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def show_checks(self, items: list[CheckItem]) -> None:
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Dynamic grouping by item.group (maintains insertion order)
        seen_groups: list[str] = []
        by_group: dict[str, list[CheckItem]] = {}
        for item in items:
            g = item.group or "Results"
            if g not in by_group:
                seen_groups.append(g)
                by_group[g] = []
            by_group[g].append(item)

        for group_title in seen_groups:
            hdr = QLabel(group_title)
            hdr.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #58a6ff;"
                " text-transform: uppercase; letter-spacing: 1px;"
                " padding: 12px 0 4px 0;"
            )
            self._layout.addWidget(hdr)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #21262d;")
            self._layout.addWidget(sep)

            for item in by_group[group_title]:
                row = _CheckRow(item)
                row.go_to_fix.connect(self.go_to_fix)
                self._layout.addWidget(row)

        self._layout.addStretch(1)

    def clear(self) -> None:
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


# ── Printer install panel ─────────────────────────────────────────────────────

class _InstallPanel(QFrame):
    """Inline install action for the 'Add Network Printer' scenario."""

    def __init__(self, runner: PowerShellRunner) -> None:
        super().__init__()
        self._runner = runner
        self._ip = ""
        self._worker: _PrinterInstallWorker | None = None
        self._admin = is_admin()

        self.setObjectName("PanelCard")
        self.setStyleSheet(
            "QFrame#PanelCard { border: 1px solid #238636; background: #0d1117; }"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(8)

        # Title
        self._title_lbl = QLabel("🖨 Install Printer")
        self._title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #f0f6fc;")
        outer.addWidget(self._title_lbl)

        # Description
        desc = QLabel(
            "Uses the best available driver: OEM driver (Canon, HP, Epson…) if already installed, "
            "otherwise falls back to the Windows built-in IPP driver. "
            "If the printer was already added with a generic driver, clicking Install updates the driver."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #c9d1d9; font-size: 12px;")
        outer.addWidget(desc)

        # What changes
        what_row = QHBoxLayout()
        what_lbl = QLabel("What changes:")
        what_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        what_row.addWidget(what_lbl)
        self._what_detail = QLabel("")
        self._what_detail.setStyleSheet("color: #9aa4b2; font-size: 11px;")
        what_row.addWidget(self._what_detail)
        what_row.addStretch(1)
        outer.addLayout(what_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #30363d;")
        outer.addWidget(sep)

        # Action row
        action_row = QHBoxLayout()
        self._result_lbl = QLabel("")
        self._result_lbl.setStyleSheet("font-size: 11px;")
        self._result_lbl.hide()
        action_row.addWidget(self._result_lbl)
        action_row.addStretch(1)

        if self._admin:
            admin_lbl = QLabel("⚠ Requires admin")
            admin_lbl.setStyleSheet("color: #d29922; font-size: 11px;")
            action_row.addWidget(admin_lbl)

            self._install_btn = QPushButton("▶ Install Printer")
            self._install_btn.setFixedWidth(140)
            self._install_btn.setStyleSheet(
                "QPushButton { background: #238636; color: white; border-radius: 4px;"
                " padding: 5px 12px; font-weight: bold; font-size: 12px; }"
                "QPushButton:hover { background: #2ea043; }"
                "QPushButton:disabled { background: #3d4249; color: #6e7681; }"
            )
            self._install_btn.clicked.connect(self._on_install)
        else:
            self._install_btn = QPushButton("▶ Install Printer")
            self._install_btn.setFixedWidth(140)
            self._install_btn.setEnabled(False)
            self._install_btn.setToolTip("Restart app as Administrator to install the printer.")
            self._install_btn.setStyleSheet(
                "QPushButton { background: #3d4249; color: #6e7681; border-radius: 4px;"
                " padding: 5px 12px; font-size: 12px; }"
            )

            restart_btn = QPushButton("🛡 Restart as Administrator")
            restart_btn.setFixedWidth(210)
            restart_btn.setStyleSheet(
                "QPushButton { background: #b45309; color: white; border: none;"
                " border-radius: 4px; padding: 5px 12px; font-weight: 600; font-size: 12px; }"
                "QPushButton:hover { background: #d97706; }"
            )
            restart_btn.clicked.connect(restart_as_admin)
            action_row.addWidget(restart_btn)

        action_row.addWidget(self._install_btn)
        outer.addLayout(action_row)

    def configure(self, ip: str) -> None:
        self._ip = ip
        self._title_lbl.setText(f"🖨 Install Printer at {ip}")
        self._what_detail.setText(
            f'TCP/IP port "IP_{ip}" + printer "Network Printer ({ip})"'
        )
        self._result_lbl.hide()
        self._install_btn.setEnabled(self._admin)
        self._install_btn.setText("▶ Install Printer")

    def _on_install(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        if not _is_valid_ipv4(self._ip):
            return

        ip = self._ip
        confirmed = QMessageBox.question(
            self,
            "Install printer?",
            f"<b>Install printer at {ip}</b><br><br>"
            f"Adds TCP/IP port <i>IP_{ip}</i> and installs printer "
            f"<i>Network Printer ({ip})</i> using the Windows built-in IPP driver.<br><br>"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return

        self._install_btn.setEnabled(False)
        self._install_btn.setText("Installing…")
        self._result_lbl.setText("Installing printer — this may take up to 30 seconds…")
        self._result_lbl.setStyleSheet("font-size: 11px; color: #8b949e;")
        self._result_lbl.show()

        self._worker = _PrinterInstallWorker(self._runner, ip)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, success: bool, message: str) -> None:
        if success:
            self._result_lbl.setText(f"✓ {message}")
            self._result_lbl.setStyleSheet("font-size: 11px; color: #3fb950; font-weight: bold;")
            self._install_btn.setText("✓ Installed")
            self._install_btn.setStyleSheet(
                "QPushButton { background: #1a4731; color: #3fb950; border-radius: 4px;"
                " padding: 5px 12px; font-size: 12px; }"
            )
        else:
            self._result_lbl.setText(f"✕ {message}")
            self._result_lbl.setStyleSheet("font-size: 11px; color: #f85149;")
            self._install_btn.setEnabled(True)
            self._install_btn.setText("▶ Retry")
        self._result_lbl.show()


# ── Remote PC checklist panel ─────────────────────────────────────────────────

class _RemotePanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        self._steps: list[RemoteStep] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # Header row
        hdr_row = QHBoxLayout()
        self._icon_lbl = QLabel("💻")
        self._icon_lbl.setStyleSheet("font-size: 18px;")
        hdr_row.addWidget(self._icon_lbl)
        self._title_lbl = QLabel("What to check on the other PC")
        self._title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #f0f6fc;")
        title = self._title_lbl
        hdr_row.addWidget(title)
        hdr_row.addStretch(1)
        self._copy_btn = QPushButton("📋 Copy as text")
        self._copy_btn.setFixedWidth(130)
        self._copy_btn.setStyleSheet(
            "QPushButton { background: #21262d; color: #c9d1d9; border: 1px solid #30363d;"
            " border-radius: 4px; padding: 4px 10px; font-size: 11px; }"
            "QPushButton:hover { background: #30363d; }"
        )
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        hdr_row.addWidget(self._copy_btn)
        lay.addLayout(hdr_row)

        subtitle = QLabel(
            "Apply these steps on the other Windows PC (as Administrator).\n"
            "Use the PowerShell commands or follow the manual instructions."
        )
        subtitle.setStyleSheet("color: #8b949e; font-size: 11px;")
        subtitle.setWordWrap(True)
        lay.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #21262d;")
        lay.addWidget(sep)

        self._steps_layout = QVBoxLayout()
        self._steps_layout.setSpacing(12)
        lay.addLayout(self._steps_layout)

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text.split(" ", 1)[1] if " " in text else text)
        self._icon_lbl.setText(text.split(" ", 1)[0])

    def load_steps(self, steps: list[RemoteStep]) -> None:
        self._steps = steps
        while self._steps_layout.count():
            child = self._steps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, step in enumerate(steps, 1):
            row = QVBoxLayout()
            row.setSpacing(3)

            label_row = QHBoxLayout()
            num = QLabel(f"{i}.")
            num.setFixedWidth(20)
            num.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 12px;")
            label_row.addWidget(num)
            lbl = QLabel(step.label)
            lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #c9d1d9;")
            label_row.addWidget(lbl, stretch=1)
            row.addLayout(label_row)

            manual = QLabel(f"  {step.manual}")
            manual.setStyleSheet("color: #8b949e; font-size: 11px;")
            manual.setWordWrap(True)
            row.addWidget(manual)

            ps_frame = QFrame()
            ps_frame.setStyleSheet(
                "QFrame { background: #0d1117; border: 1px solid #21262d;"
                " border-radius: 4px; padding: 2px; }"
            )
            ps_lay = QHBoxLayout(ps_frame)
            ps_lay.setContentsMargins(8, 4, 8, 4)
            ps_lbl = QLabel(step.ps_cmd)
            ps_lbl.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; color: #79c0ff;")
            ps_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            ps_lay.addWidget(ps_lbl, stretch=1)
            row.addWidget(ps_frame)

            container = QWidget()
            container.setLayout(row)
            self._steps_layout.addWidget(container)

    def _copy_to_clipboard(self) -> None:
        if not self._steps:
            return
        lines = ["What to check on the other PC (run as Administrator in PowerShell):\n"]
        for i, step in enumerate(self._steps, 1):
            lines.append(f"{i}. {step.label}")
            lines.append(f"   {step.manual}")
            lines.append(f"   PS> {step.ps_cmd}")
            lines.append("")
        QGuiApplication.clipboard().setText("\n".join(lines))
        self._copy_btn.setText("✓ Copied!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._copy_btn.setText("📋 Copy as text"))


# ── Main page ─────────────────────────────────────────────────────────────────

class ScenariosPage(QWidget):
    open_fix_center = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._runner = PowerShellRunner()
        self._worker: _ScenarioWorker | None = None
        self._active_scenario: Scenario | None = None
        self._last_result: ScanResult | None = None

        self._build_ui()
        self._select_scenario(ALL_SCENARIOS[0])

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        hdr_row = QHBoxLayout()
        title = QLabel("🗂 Guided Scenarios")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f0f6fc;")
        hdr_row.addWidget(title)
        hdr_row.addStretch(1)
        root.addLayout(hdr_row)

        subtitle = QLabel("Select a scenario to run a targeted diagnostic and get step-by-step guidance.")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px;")
        root.addWidget(subtitle)

        # Scenario cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._cards: dict[str, _ScenarioCard] = {}
        for s in ALL_SCENARIOS:
            card = _ScenarioCard(s)
            card.selected.connect(self._select_scenario)
            cards_row.addWidget(card)
            self._cards[s.id] = card
        cards_row.addStretch(1)
        root.addLayout(cards_row)

        # Detail panel
        self._detail_panel = QFrame()
        self._detail_panel.setObjectName("PanelCard")
        detail_lay = QVBoxLayout(self._detail_panel)
        detail_lay.setContentsMargins(20, 16, 20, 16)
        detail_lay.setSpacing(10)

        self._scenario_title = QLabel()
        self._scenario_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f0f6fc;")
        detail_lay.addWidget(self._scenario_title)

        self._scenario_desc = QLabel()
        self._scenario_desc.setWordWrap(True)
        self._scenario_desc.setStyleSheet("color: #c9d1d9; font-size: 12px;")
        detail_lay.addWidget(self._scenario_desc)

        # Target IP input
        ip_row = QHBoxLayout()
        self._ip_lbl = QLabel("Target PC IP (optional):")
        self._ip_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        ip_row.addWidget(self._ip_lbl)
        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g. 192.168.1.100")
        self._ip_input.setMaximumWidth(200)
        self._ip_input.setStyleSheet(
            "QLineEdit { background: #0d1117; border: 1px solid #30363d;"
            " border-radius: 4px; padding: 4px 8px; color: #f0f6fc; font-size: 12px; }"
            "QLineEdit:focus { border-color: #58a6ff; }"
        )
        ip_row.addWidget(self._ip_input)

        self._tip_lbl = QLabel()
        self._tip_lbl.setStyleSheet("color: #6e7681; font-size: 11px; font-style: italic;")
        ip_row.addWidget(self._tip_lbl)
        ip_row.addStretch(1)
        detail_lay.addLayout(ip_row)

        # Run button + status
        run_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Run Diagnostic")
        self._run_btn.setFixedWidth(160)
        self._run_btn.setStyleSheet(
            "QPushButton { background: #1f6feb; color: white; border-radius: 6px;"
            " padding: 7px 16px; font-weight: bold; font-size: 13px; }"
            "QPushButton:hover { background: #388bfd; }"
            "QPushButton:disabled { background: #21262d; color: #6e7681; }"
        )
        self._run_btn.clicked.connect(self._run_diagnostic)
        run_row.addWidget(self._run_btn)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        run_row.addWidget(self._status_lbl)
        run_row.addStretch(1)
        detail_lay.addLayout(run_row)

        root.addWidget(self._detail_panel)

        # Results scroll area
        results_container = QWidget()
        self._results_layout = QVBoxLayout(results_container)
        self._results_layout.setContentsMargins(0, 0, 0, 0)

        self._results_panel = _ResultsPanel()
        self._results_panel.go_to_fix.connect(self._on_go_to_fix)
        self._results_layout.addWidget(self._results_panel)

        self._discovery_panel = _PrinterDiscoveryPanel(self._runner)
        self._discovery_panel.printer_selected.connect(self._on_printer_selected)
        self._discovery_panel.hide()
        self._results_layout.addWidget(self._discovery_panel)

        self._install_panel = _InstallPanel(self._runner)
        self._install_panel.hide()
        self._results_layout.addWidget(self._install_panel)

        self._remote_panel = _RemotePanel()
        self._remote_panel.hide()
        self._results_layout.addWidget(self._remote_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(results_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll, stretch=1)

    def _select_scenario(self, scenario: Scenario) -> None:
        self._active_scenario = scenario
        for sid, card in self._cards.items():
            card.set_active(sid == scenario.id)

        self._scenario_title.setText(f"{scenario.icon}  {scenario.title}")
        self._scenario_desc.setText(scenario.description)
        self._tip_lbl.setText(scenario.tip)
        self._results_panel.clear()
        self._status_lbl.setText("")
        self._discovery_panel.hide()
        self._install_panel.hide()
        self._remote_panel.hide()

        if scenario.id == "add_network_printer":
            self._ip_lbl.setText("Printer IP:")
            self._ip_input.setPlaceholderText("e.g. 192.168.1.50")
        else:
            self._ip_lbl.setText("Target PC IP (optional):")
            self._ip_input.setPlaceholderText("e.g. 192.168.1.100")

    def _run_diagnostic(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        if not self._active_scenario:
            return

        target_ip = self._ip_input.text().strip()
        self._run_btn.setEnabled(False)
        self._status_lbl.setText("Scanning…")
        self._results_panel.clear()
        self._discovery_panel.hide()
        self._install_panel.hide()
        self._remote_panel.hide()

        self._worker = _ScenarioWorker(self._runner, target_ip)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, msg: str) -> None:
        self._status_lbl.setText(msg)

    def _on_finished(self, result: ScanResult) -> None:
        self._last_result = result
        self._run_btn.setEnabled(True)

        target_ip = self._ip_input.text().strip()
        checks = run_checks(self._active_scenario, result, target_ip)

        passed = sum(1 for c in checks if c.passed)
        total = len(checks)
        issues = total - passed

        if issues == 0:
            self._status_lbl.setText(f"✓ All {total} checks passed — ready to connect!")
            self._status_lbl.setStyleSheet("color: #3fb950; font-size: 12px;")
        else:
            self._status_lbl.setText(f"{issues} issue(s) found — see details below.")
            self._status_lbl.setStyleSheet("color: #d29922; font-size: 12px;")

        self._results_panel.show_checks(checks)

        if self._active_scenario.id == "add_network_printer":
            already_installed = any(
                c.passed and "already installed" in c.label
                for c in checks
            )
            # Show discover panel always for printer scenario
            self._discovery_panel.show()

            if not already_installed and _is_valid_ipv4(target_ip):
                self._install_panel.configure(target_ip)
                self._install_panel.show()
            else:
                self._install_panel.hide()
            self._remote_panel.hide()
        else:
            self._discovery_panel.hide()
            self._install_panel.hide()
            remote_steps = run_remote_checklist(self._active_scenario)
            if remote_steps:
                self._remote_panel.set_title("💻 What to check on the other PC")
                self._remote_panel.load_steps(remote_steps)
                self._remote_panel.show()
            else:
                self._remote_panel.hide()

    def _on_printer_selected(self, ip: str, name: str) -> None:
        self._ip_input.setText(ip)
        self._install_panel.configure(ip)
        self._install_panel.show()

    def _on_go_to_fix(self, _fix_id: str) -> None:
        self.open_fix_center.emit()
