from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.core.issue import Issue
from app.core.risk_level import RiskLevel

_SHIELD_COLOR = {
    RiskLevel.CRITICAL: "#f85149",
    RiskLevel.HIGH:     "#d29922",
    RiskLevel.MEDIUM:   "#58a6ff",
    RiskLevel.LOW:      "#3fb950",
}


def _build_row(title: str, severity) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(8)

    shield_color = _SHIELD_COLOR.get(severity, "#58a6ff")
    shield = QLabel("🛡")
    shield.setStyleSheet(f"color: {shield_color};")
    shield.setFixedWidth(20)
    row.addWidget(shield)

    lbl = QLabel(title)
    lbl.setWordWrap(False)
    lbl.setStyleSheet("font-size: 12px;")
    row.addWidget(lbl, stretch=1)

    # "Review" navigates to Fix Center — never executes fix directly (architecture rule)
    review_btn = QPushButton("Apply")
    review_btn.setFixedWidth(60)
    review_btn.setStyleSheet(
        "QPushButton { background-color: #1a7f37; color: white; border: none;"
        " border-radius: 5px; padding: 4px 10px; font-size: 11px; font-weight: 600; }"
        "QPushButton:hover { background-color: #2ea043; }"
    )
    review_btn.setToolTip("Opens Fix Center for review before applying")
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

        self._fix_center_btn = QPushButton("🔧  Open Fix Center (Detailed Fixes)  ›")
        self._fix_center_btn.setStyleSheet(
            "QPushButton { background-color: #0d2840; color: #58a6ff; border: 1px solid #1f4060;"
            " border-radius: 6px; padding: 8px 16px; font-weight: 600; text-align: left; }"
            "QPushButton:hover { background-color: #102a4a; border-color: #2d6da8; color: #79b8ff; }"
        )
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
            self._content.addLayout(_build_row(issue.title, issue.severity))
