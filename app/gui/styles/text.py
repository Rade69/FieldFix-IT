"""Small helpers for local QLabel text styles."""

from __future__ import annotations

TEXT_PRIMARY = "#1F2937"
TEXT_HEADING = "#111827"
TEXT_SECONDARY = "#64748B"
TEXT_DISABLED = "#6B7280"


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
