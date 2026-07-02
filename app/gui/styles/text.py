"""Small helpers for local QLabel text styles."""

from __future__ import annotations

from app.gui.styles.palette import DARK

TEXT_PRIMARY = DARK["text"]
TEXT_HEADING = DARK["text_heading"]
TEXT_SECONDARY = DARK["text_secondary"]
TEXT_DISABLED = DARK["text_disabled"]


def text_style(
    color: str = TEXT_SECONDARY,
    *,
    size: int | None = None,
    weight: int | str | None = None,
    family: str | None = None,
    italic: bool = False,
    border: str | None = None,
) -> str:
    parts = [f"color: {color};"]
    if size is not None:
        parts.append(f"font-size: {size}px;")
    if weight is not None:
        parts.append(f"font-weight: {weight};")
    if family is not None:
        parts.append(f"font-family: {family};")
    if italic:
        parts.append("font-style: italic;")
    if border is not None:
        parts.append(f"border: {border};")
    return " ".join(parts)


def secondary_text_style(*, size: int | None = None, weight: int | str | None = None) -> str:
    return text_style(TEXT_SECONDARY, size=size, weight=weight)


def disabled_text_style(*, size: int | None = None) -> str:
    return text_style(TEXT_DISABLED, size=size)
