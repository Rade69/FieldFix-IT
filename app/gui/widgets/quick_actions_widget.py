from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.core.risk_level import RiskLevel
from app.gui.widgets.risk_badge import RiskBadge

# Dummy data only — replaced by real Recommendation objects once Fix Center exists (Faza 13).
_DUMMY_ACTIONS = [
    ("Enable File and Printer Sharing (FW)", RiskLevel.LOW),
    ("Enable Network Discovery (FW)", RiskLevel.LOW),
    ("Set Network Profile to Private", RiskLevel.LOW),
    ("Start Required Services", RiskLevel.LOW),
]


def _build_row(title: str, risk: RiskLevel) -> QHBoxLayout:
    row = QHBoxLayout()
    icon = QLabel("🛡")
    title_label = QLabel(title)
    row.addWidget(icon)
    row.addWidget(title_label)
    row.addWidget(RiskBadge(str(risk)))
    row.addStretch(1)
    review_button = QPushButton("Review")
    row.addWidget(review_button)
    return row


class QuickActionsWidget(QFrame):
    """Quick Actions panel.

    Buttons say "Review", never "Apply" — Dashboard must never execute a fix
    directly (see docs/architecture_notes.md, "Dashboard: Review Fix, ne
    Apply"). Inert until Fix Center (Faza 13) wires the real review/apply flow.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("⚡ Quick Actions (Fix Mode)")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        for action_title, risk in _DUMMY_ACTIONS:
            layout.addLayout(_build_row(action_title, risk))

        open_fix_center_button = QPushButton("🔧 Open Fix Center (Detailed Fixes)")
        layout.addWidget(open_fix_center_button)
