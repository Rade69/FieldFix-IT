import sys
from pathlib import Path


def _base() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


_ICONS_DIR = _base() / "resources" / "icons"

APP_ICON_ICO = _ICONS_DIR / "fieldfix_icon.ico"
APP_ICON_16 = _ICONS_DIR / "fieldfix_icon_16.png"
APP_ICON_32 = _ICONS_DIR / "fieldfix_icon_32.png"
APP_ICON_64 = _ICONS_DIR / "fieldfix_icon_64.png"
APP_ICON_128 = _ICONS_DIR / "fieldfix_icon_128.png"
APP_ICON_256 = _ICONS_DIR / "fieldfix_icon_256.png"

UI_ICON_DASHBOARD = _ICONS_DIR / "ui" / "dashboard.svg"
UI_ICON_NETWORK = _ICONS_DIR / "ui" / "network.svg"
UI_ICON_SMB = _ICONS_DIR / "ui" / "smb.svg"
UI_ICON_FIREWALL = _ICONS_DIR / "ui" / "firewall.svg"
UI_ICON_SERVICES = _ICONS_DIR / "ui" / "services.svg"
UI_ICON_PRINTERS = _ICONS_DIR / "ui" / "printers.svg"
UI_ICON_TOPOLOGY = _ICONS_DIR / "ui" / "topology.svg"
UI_ICON_FIX = _ICONS_DIR / "ui" / "fix.svg"
UI_ICON_REPORTS = _ICONS_DIR / "ui" / "reports.svg"
UI_ICON_SETTINGS = _ICONS_DIR / "ui" / "settings.svg"
UI_ICON_ABOUT = _ICONS_DIR / "ui" / "about.svg"
UI_ICON_ISSUES = _ICONS_DIR / "ui" / "issues.svg"
UI_ICON_SCAN = _ICONS_DIR / "ui" / "scan.svg"
UI_ICON_DESKTOP = _ICONS_DIR / "ui" / "desktop.svg"

UI_ICONS = {
    "Dashboard": UI_ICON_DASHBOARD,
    "Network": UI_ICON_NETWORK,
    "SMB": UI_ICON_SMB,
    "Sharing / SMB": UI_ICON_SMB,
    "Firewall": UI_ICON_FIREWALL,
    "Services": UI_ICON_SERVICES,
    "Printers": UI_ICON_PRINTERS,
    "Topology": UI_ICON_TOPOLOGY,
    "Fix Center": UI_ICON_FIX,
    "Reports": UI_ICON_REPORTS,
    "Settings": UI_ICON_SETTINGS,
    "About": UI_ICON_ABOUT,
    "Issues": UI_ICON_ISSUES,
    "Scan": UI_ICON_SCAN,
    "Desktop": UI_ICON_DESKTOP,
}
