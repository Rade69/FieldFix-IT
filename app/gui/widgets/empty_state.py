"""Shared helpers for empty-state banners and scan-context messages."""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from app.gui.styles import TEXT_SECONDARY, text_style


def info_banner(message: str, hint: str = "", level: str = "info") -> QFrame:
    """Inline banner used for empty states, scan errors, and context hints.

    level: "info" | "warning" | "error"
    """
    _color = {"info": "#1f6feb", "warning": "#d29922", "error": "#f85149"}
    _icon  = {"info": "ℹ", "warning": "⚠", "error": "✕"}
    color  = _color.get(level, TEXT_SECONDARY)
    icon   = _icon.get(level, "ℹ")

    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{ border: none; border-left: 3px solid {color};"
        f" background: transparent; }}"
    )
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 8, 8, 8)
    lay.setSpacing(3)

    msg_lbl = QLabel(f"{icon}  {message}")
    msg_lbl.setStyleSheet(
        f"color: {color}; font-weight: 600; font-size: 12px; border: none;"
    )
    msg_lbl.setWordWrap(True)
    lay.addWidget(msg_lbl)

    if hint:
        hint_lbl = QLabel(hint)
        hint_lbl.setStyleSheet(text_style(size=11, border="none"))
        hint_lbl.setWordWrap(True)
        lay.addWidget(hint_lbl)

    return frame
