"""Compatibility wrapper for the centralized GUI styles package."""

from app.gui.styles.theme import (
    DARK_STYLESHEET,
    LIGHT_STYLESHEET,
    get_stylesheet,
    normalize_theme,
)

__all__ = [
    "DARK_STYLESHEET",
    "LIGHT_STYLESHEET",
    "get_stylesheet",
    "normalize_theme",
]
