"""Application settings — persisted to %APPDATA%/FieldFix IT/settings.json."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path


def _default_reports_dir() -> str:
    return str(Path.home() / "Desktop")


def _settings_path() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    return Path(appdata) / "FieldFix IT" / "settings.json"


@dataclass
class AppSettings:
    # ── Scanning ──────────────────────────────────────────────────────────────
    scan_network:         bool = True
    scan_smb:             bool = True
    scan_services:        bool = True
    scan_printers:        bool = True
    scan_timeout_sec:     int  = 30
    auto_scan_on_startup: bool = False
    max_topology_devices: int  = 8

    # ── Reports ───────────────────────────────────────────────────────────────
    reports_dir:      str  = field(default_factory=_default_reports_dir)
    reports_format:   str  = "html"   # html | markdown | json
    auto_open_report: bool = False

    # ── Safety ────────────────────────────────────────────────────────────────
    # confirm_before_apply is always True — displayed read-only so the user
    # understands the confirmation dialog is intentional, not a bug.
    confirm_before_apply: bool = True

    def save(self) -> None:
        p = _settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> AppSettings:
        p = _settings_path()
        if not p.exists():
            return cls()
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            known = {f.name for f in fields(cls)}
            return cls(**{k: v for k, v in raw.items() if k in known})
        except Exception:
            return cls()


# Module-level singleton — defined after the class to avoid forward-ref issues.
_instance: AppSettings | None = None


def get_settings() -> AppSettings:
    """Return the app-wide settings singleton, loading from disk on first call."""
    global _instance
    if _instance is None:
        _instance = AppSettings.load()
    return _instance


def reload_settings() -> AppSettings:
    """Force reload from disk and update the singleton."""
    global _instance
    _instance = AppSettings.load()
    return _instance
