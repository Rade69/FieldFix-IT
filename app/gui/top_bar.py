from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.core.powershell_runner import PowerShellRunner
from app.gui.icons import APP_ICON_32
from app.modules.network.models import NetworkData


@dataclass(frozen=True)
class _SysInfo:
    os_caption: str       # "Windows 11 Pro"
    build_number: str     # "22631"
    ubr: str              # "3296"
    release_label: str    # "23H2"
    uptime_seconds: int
    ip_address: str
    network_name: str
    network_category: str  # "Private" | "Public" | "DomainAuthenticated"


_CATEGORY_COLOR = {
    "Private": "#3fb950",
    "DomainAuthenticated": "#58a6ff",
    "Public": "#d29922",
}

_PS_SYSINFO = r"""
$os  = Get-CimInstance Win32_OperatingSystem
$net = Get-NetConnectionProfile -ErrorAction SilentlyContinue | Select-Object -First 1
$ip  = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike '169.*' -and $_.IPAddress -ne '127.0.0.1' } |
        Select-Object -First 1).IPAddress
$cv  = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' `
       -ErrorAction SilentlyContinue
[PSCustomObject]@{
    OsCaption       = ($os.Caption -replace 'Microsoft ', '')
    BuildNumber     = [string]$os.BuildNumber
    UBR             = if ($cv.UBR)           { [string]$cv.UBR }           else { '0' }
    ReleaseLabel    = if ($cv.DisplayVersion) { $cv.DisplayVersion }        else { '' }
    UptimeSeconds   = [int]((Get-Date) - $os.LastBootUpTime).TotalSeconds
    IPAddress       = if ($ip)               { $ip }                        else { '' }
    NetworkName     = if ($net)              { [string]$net.Name }          else { '' }
    NetworkCategory = if ($net)              { [string]$net.NetworkCategory } else { '' }
} | ConvertTo-Json -Compress
"""


def _fetch_sysinfo(runner: PowerShellRunner) -> _SysInfo:
    result = runner.run_json(_PS_SYSINFO.strip(), timeout=15)
    if result.succeeded and isinstance(result.parsed_json, dict):
        d = result.parsed_json
        return _SysInfo(
            os_caption=str(d.get("OsCaption", "Windows")),
            build_number=str(d.get("BuildNumber", "")),
            ubr=str(d.get("UBR", "0")),
            release_label=str(d.get("ReleaseLabel", "")),
            uptime_seconds=int(d.get("UptimeSeconds") or 0),
            ip_address=str(d.get("IPAddress") or ""),
            network_name=str(d.get("NetworkName") or ""),
            network_category=str(d.get("NetworkCategory") or ""),
        )
    v = sys.getwindowsversion()
    return _SysInfo(
        os_caption="Windows 11" if v.build >= 22000 else "Windows 10",
        build_number=str(v.build),
        ubr="",
        release_label="",
        uptime_seconds=0,
        ip_address="",
        network_name="",
        network_category="",
    )


def _format_uptime(sec: int) -> str:
    if sec <= 0:
        return "—"
    d, r = divmod(sec, 86400)
    h, r = divmod(r, 3600)
    m = r // 60
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def _os_display(info: _SysInfo) -> str:
    parts = [info.os_caption]
    if info.release_label:
        parts.append(info.release_label)
    if info.build_number:
        ubr = f".{info.ubr}" if info.ubr and info.ubr != "0" else ""
        parts.append(f"({info.build_number}{ubr})")
    return " ".join(parts)


def _net_html(name: str, category: str) -> str:
    color = _CATEGORY_COLOR.get(category, "#9aa4b2")
    if not name and not category:
        return "Network: —"
    parts = ["Network:"]
    if name:
        parts.append(name)
    if category:
        parts.append(f'<span style="color:{color};">({category})</span>')
    return " ".join(parts)


def _rich(html: str, muted: bool = False) -> QLabel:
    lbl = QLabel(html)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    if muted:
        lbl.setStyleSheet("color: #9aa4b2; font-size: 11px;")
    return lbl


class TopBar(QFrame):
    """Global header bar. Populates with real system data via a single PS call at startup."""

    open_settings = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TopBar")

        info = _fetch_sysinfo(PowerShellRunner())

        computer = os.environ.get("COMPUTERNAME", "Unknown")
        user = os.environ.get("USERNAME", "Unknown")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 12, 22, 12)
        layout.setSpacing(0)

        # App icon + title
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(str(APP_ICON_32)).scaled(
            42, 42,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        layout.addWidget(icon_label)
        layout.addSpacing(10)

        logo_col = QVBoxLayout()
        logo_col.setSpacing(2)
        title = QLabel("FieldFix IT")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f0f6fc;")
        logo_col.addWidget(title)
        logo_col.addWidget(_rich("Windows IT Diagnostics", muted=True))
        layout.addLayout(logo_col)
        layout.addSpacing(34)

        # Left block: computer name + OS / user / uptime
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        left_col.addWidget(_rich(f"Computer: <b>{computer}</b>"))
        self._detail_label = _rich(
            f"{_os_display(info)} &nbsp;&nbsp; User: {user}"
            f" &nbsp;&nbsp; Uptime: {_format_uptime(info.uptime_seconds)}",
            muted=True,
        )
        left_col.addWidget(self._detail_label)
        layout.addLayout(left_col)
        layout.addSpacing(34)

        # Right block: IP + network
        right_col = QVBoxLayout()
        right_col.setSpacing(2)
        self._ip_label = _rich(f"IP: <b>{info.ip_address or '—'}</b>")
        right_col.addWidget(self._ip_label)
        self._net_label = _rich(
            _net_html(info.network_name, info.network_category), muted=True
        )
        right_col.addWidget(self._net_label)
        layout.addLayout(right_col)
        layout.addStretch(1)

        # Scan Mode badge
        scan_mode = QFrame()
        scan_mode.setObjectName("ScanModeBadge")
        sm_layout = QVBoxLayout(scan_mode)
        sm_layout.setContentsMargins(16, 6, 16, 6)
        sm_layout.setSpacing(0)
        sm_layout.addWidget(_rich("🛡 Scan Mode", muted=True))
        sm_val = QLabel("Read Only")
        sm_val.setStyleSheet("color: #3fb950; font-weight: bold;")
        sm_layout.addWidget(sm_val)
        layout.addWidget(scan_mode)
        layout.addSpacing(16)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #9aa4b2; border: none; }"
            "QPushButton:hover { color: #f0f6fc; }"
        )
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        layout.addSpacing(16)

        layout.addWidget(QPushButton("▶ Start New Scan ▾"))

    def update_network(self, network: NetworkData | None) -> None:
        """Refresh IP and network labels after a Dashboard scan completes."""
        if network is None:
            return
        ipv4 = next(
            (ip.ip_address for ip in network.ip_addresses if "." in ip.ip_address),
            None,
        )
        if ipv4:
            self._ip_label.setText(f"IP: <b>{ipv4}</b>")
        if network.profiles:
            p = network.profiles[0]
            self._net_label.setText(_net_html(p.name, p.category))
