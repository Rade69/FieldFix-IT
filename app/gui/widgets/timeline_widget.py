from __future__ import annotations

from typing import NamedTuple

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class TimelineEvent(NamedTuple):
    time: str
    icon: str
    color: str
    message: str
    detail: str


def _build_row(event: TimelineEvent) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(10)

    time_lbl = QLabel(event.time)
    time_lbl.setStyleSheet("color: #6B7280; font-size: 11px; font-family: monospace;")
    time_lbl.setFixedWidth(56)
    row.addWidget(time_lbl)

    icon_lbl = QLabel(event.icon)
    icon_lbl.setStyleSheet(f"color: {event.color};")
    icon_lbl.setFixedWidth(16)
    row.addWidget(icon_lbl)

    msg_lbl = QLabel(event.message)
    msg_lbl.setStyleSheet("font-weight: bold;")
    row.addWidget(msg_lbl)
    row.addStretch(1)

    detail_lbl = QLabel(event.detail)
    detail_lbl.setStyleSheet("color: #6B7280; font-size: 11px;")
    row.addWidget(detail_lbl)

    return row


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if w := item.widget():
            w.deleteLater()
        elif child := item.layout():
            _clear_layout(child)


class ActivityTimelineWidget(QFrame):
    """Activity Timeline panel. Populated by update_data() after scan."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        title = QLabel("📋 Activity Timeline")
        title.setStyleSheet("font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        clear_link = QLabel("⟲ Clear")
        clear_link.setStyleSheet("color: #2563EB;")
        header_row.addWidget(clear_link)
        layout.addLayout(header_row)

        self._content = QVBoxLayout()
        self._content.setSpacing(6)
        layout.addLayout(self._content)
        layout.addStretch(1)

        self._placeholder()

    def _placeholder(self) -> None:
        lbl = QLabel("No scan results yet.")
        lbl.setStyleSheet("color: #6B7280;")
        self._content.addWidget(lbl)

    def update_data(self, events: list[TimelineEvent]) -> None:
        _clear_layout(self._content)
        if not events:
            self._placeholder()
            return
        for event in events:
            self._content.addLayout(_build_row(event))
