import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap


def _base() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


_ICONS_DIR = _base() / "resources" / "icons"

APP_ICON_ICO = _ICONS_DIR / "fieldfix_icon.ico"
APP_ICON_16  = _ICONS_DIR / "fieldfix_icon_16.png"
APP_ICON_32  = _ICONS_DIR / "fieldfix_icon_32.png"
APP_ICON_64  = _ICONS_DIR / "fieldfix_icon_64.png"
APP_ICON_128 = _ICONS_DIR / "fieldfix_icon_128.png"
APP_ICON_256 = _ICONS_DIR / "fieldfix_icon_256.png"

# ── Segoe MDL2 Assets codepoints ─────────────────────────────────────────────
# Built into every Windows 10/11 — no download, no licence, no extra files.
SEGOE_MDL2: dict[str, str] = {
    "Dashboard":     "",  # DashView      — 4 kvadrata
    "Network":       "",  # Globe2        — mreža/internet
    "Sharing / SMB": "",  # SharedPC      — dijeljenje
    "SMB":           "",
    "Firewall":      "",  # Lock          — sigurnost/firewall
    "Services":      "",  # Processing    — zupčanik u toku
    "Printers":      "",  # Print         — štampač
    "Topology":      "",  # Map           — karta/topologija
    "Fix Center":    "",  # RepairService — ključ/popravak
    "Reports":       "",  # Page          — dokument
    "Settings":      "",  # Settings      — zupčanik
    "About":         "",  # Contact2      — info krug
    "Issues":        "",  # Important     — trokut upozorenje
    "Scan":          "",  # Search        — lupa
    "Desktop":       "",  # PC/Desktop
}

# SVG paths from the Phosphor set.
_UI = _ICONS_DIR / "ui"
PHOSPHOR_UI_ICONS: dict[str, Path] = {
    "Dashboard":     _UI / "dashboard.svg",
    "Network":       _UI / "network.svg",
    "SMB":           _UI / "smb.svg",
    "Sharing / SMB": _UI / "smb.svg",
    "Firewall":      _UI / "firewall.svg",
    "Services":      _UI / "services.svg",
    "Printers":      _UI / "printers.svg",
    "Topology":      _UI / "topology.svg",
    "Scenarios":     _UI / "scenarios.svg",
    "Fix Center":    _UI / "fix.svg",
    "Reports":       _UI / "reports.svg",
    "Settings":      _UI / "settings.svg",
    "About":         _UI / "about.svg",
    "Issues":        _UI / "issues.svg",
    "Scan":          _UI / "scan.svg",
    "Desktop":       _UI / "desktop.svg",
}

# PNG icons extracted from the GUI mockup sprite.
_MOCKUP = _ICONS_DIR / "mockup"
_MOCKUP_ICON_NAMES = (
    "about",
    "action_required",
    "apply",
    "arrow_right",
    "computer",
    "connection",
    "connection_inactive",
    "dashboard",
    "database",
    "date",
    "device_offline",
    "device_online",
    "device_printer",
    "device_server",
    "device_unknown",
    "domain",
    "dropdown",
    "export",
    "file_issue",
    "firewall",
    "firewall_ok",
    "firewall_warning",
    "fix_mode",
    "internet",
    "ip_address",
    "issue_critical",
    "issue_info",
    "issue_warning",
    "issues",
    "log",
    "mac_address",
    "network",
    "network_error",
    "network_issue",
    "network_ok",
    "network_other",
    "open_details",
    "open_fix_center",
    "open_network_map",
    "printer_device",
    "printers",
    "printers_status",
    "quick_action",
    "recommend_ok",
    "recommendation",
    "refresh",
    "reports",
    "router",
    "scan_mode_read_only",
    "security_issue",
    "server",
    "services",
    "services_ok",
    "settings",
    "sharing",
    "sharing_error",
    "sharing_ok",
    "smb_issue",
    "start_scan",
    "status_error",
    "status_ok",
    "status_warning",
    "theme_dark",
    "theme_light",
    "time",
    "topology",
    "user",
    "view_all",
)
MOCKUP_ICONS: dict[str, Path] = {
    name: _MOCKUP / f"{name}.png" for name in _MOCKUP_ICON_NAMES
}
MOCKUP_ICONS.update(
    {
        "Dashboard": MOCKUP_ICONS["dashboard"],
        "Network": MOCKUP_ICONS["network"],
        "SMB": MOCKUP_ICONS["sharing"],
        "Sharing / SMB": MOCKUP_ICONS["sharing"],
        "Firewall": MOCKUP_ICONS["firewall"],
        "Services": MOCKUP_ICONS["services"],
        "Printers": MOCKUP_ICONS["printers"],
        "Topology": MOCKUP_ICONS["topology"],
        "Fix Center": MOCKUP_ICONS["open_fix_center"],
        "Reports": MOCKUP_ICONS["reports"],
        "Settings": MOCKUP_ICONS["settings"],
        "About": MOCKUP_ICONS["about"],
        "Issues": MOCKUP_ICONS["issues"],
        "Scan": MOCKUP_ICONS["start_scan"],
        "Desktop": MOCKUP_ICONS["computer"],
    }
)

NAV_ICONS: dict[str, Path] = PHOSPHOR_UI_ICONS | {
    key: MOCKUP_ICONS[key]
    for key in (
        "Dashboard",
        "Network",
        "SMB",
        "Sharing / SMB",
        "Firewall",
        "Services",
        "Printers",
        "Topology",
        "Fix Center",
        "Reports",
        "Settings",
        "About",
        "Issues",
        "Scan",
        "Desktop",
    )
}

STATUS_CARD_ICONS: dict[str, Path] = PHOSPHOR_UI_ICONS | {
    "Network": MOCKUP_ICONS["network_ok"],
    "SMB": MOCKUP_ICONS["sharing_ok"],
    "Sharing / SMB": MOCKUP_ICONS["sharing_ok"],
    "Firewall": MOCKUP_ICONS["firewall_warning"],
    "Services": MOCKUP_ICONS["services_ok"],
    "Printers": MOCKUP_ICONS["printers_status"],
    "Issues": MOCKUP_ICONS["issues"],
}

# Backwards-compatible public lookup used by older widgets.
UI_ICONS: dict[str, Path] = NAV_ICONS


def mockup_icon_path(name: str) -> Path | None:
    """Return a mockup-derived icon path by alias or file stem."""
    return MOCKUP_ICONS.get(name)


def icon_from_glyph(
    glyph: str,
    size: int = 24,
    color: str = "#8fc7ff",
    font_name: str = "Segoe MDL2 Assets",
) -> QIcon:
    """Render a font glyph onto a transparent QPixmap and return as QIcon.

    Produces crisp icons at any size without external SVG files.
    Returns an empty QIcon if the glyph string is empty.
    """
    if not glyph:
        return QIcon()
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    font = QFont(font_name)
    font.setPixelSize(int(size * 0.72))
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
    painter.end()
    return QIcon(px)


def segoe_icon(name: str, size: int = 24, color: str = "#8fc7ff") -> QIcon:
    """Return a Segoe MDL2 QIcon for the given page/widget name."""
    return icon_from_glyph(SEGOE_MDL2.get(name, ""), size=size, color=color)
