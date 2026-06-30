from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.core.issue import Issue
from app.gui.widgets.risk_badge import RiskBadge


def _build_row(title: str, severity_str: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addWidget(QLabel("🛡"))
    lbl = QLabel(title)
    lbl.setWordWrap(False)
    row.addWidget(lbl)
    row.addWidget(RiskBadge(severity_str))
    row.addStretch(1)
    review_btn = QPushButton("Review")
    # Review is inert until Fix Center is wired (Faza 13).
    row.addWidget(review_btn)
    return row


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if w := item.widget():
            w.deleteLater()
        elif child := item.layout():
            _clear_layout(child)


class QuickActionsWidget(QFrame):
    """Quick Actions panel. Review buttons are inert until Fix Center (Faza 13).

    Dashboard must never execute a fix directly — see docs/architecture_notes.md.
    """

    open_fix_center = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("⚡ Quick Actions (Fix Mode)")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self._content = QVBoxLayout()
        layout.addLayout(self._content)
        self._placeholder()

        self._fix_center_btn = QPushButton("🔧 Open Fix Center (Detailed Fixes)")
        self._fix_center_btn.clicked.connect(self.open_fix_center)
        layout.addWidget(self._fix_center_btn)

    def _placeholder(self) -> None:
        lbl = QLabel("Run a scan to see recommended actions.")
        lbl.setStyleSheet("color: #9aa4b2;")
        self._content.addWidget(lbl)

    def update_data(self, issues: tuple[Issue, ...]) -> None:
        _clear_layout(self._content)
        if not issues:
            lbl = QLabel("✓ No actions required.")
            lbl.setStyleSheet("color: #3fb950;")
            self._content.addWidget(lbl)
            return
        for issue in issues[:4]:  # top 4 issues as review actions
            self._content.addLayout(_build_row(issue.title, str(issue.severity)))
