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
