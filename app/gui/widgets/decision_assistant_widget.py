from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

# Dummy data only — replaced by Decision Engine output (Faza 10).
_DUMMY_STEPS = [
    ("Ping Host", "✓", "#3fb950"),
    ("SMB Port", "✓", "#3fb950"),
    ("Authentication", "✕", "#f85149"),
    ("Access", "○", "#9aa4b2"),
]

_DUMMY_PROBLEM = "Cannot access \\\\192.168.100.155?"
_DUMMY_CONCLUSION = "Wrong credentials or insufficient permissions."


def _build_step_chain(steps: list) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setAlignment(Qt.AlignmentFlag.AlignLeft)
    row.setSpacing(4)

    for i, (label, icon, color) in enumerate(steps):
        step_col = QVBoxLayout()
        step_col.setSpacing(2)
        step_col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 18px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        step_col.addWidget(icon_label)

        name_label = QLabel(label)
        name_label.setStyleSheet("font-size: 10px; color: #9aa4b2;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        step_col.addWidget(name_label)

        row.addLayout(step_col)

        if i < len(steps) - 1:
            arrow = QLabel("→")
            arrow.setStyleSheet("color: #9aa4b2; font-size: 14px;")
            arrow.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(arrow)

    row.addStretch(1)
    return row


class DecisionAssistantWidget(QFrame):
    """Decision Assistant panel. Dummy diagnostic chain — replaced by Decision Engine (Faza 10)."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("🤖 Decision Assistant")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        problem_label = QLabel(_DUMMY_PROBLEM)
        problem_label.setStyleSheet("color: #9aa4b2; font-size: 11px;")
        layout.addWidget(problem_label)

        layout.addLayout(_build_step_chain(_DUMMY_STEPS))

        cause_label = QLabel("Most likely cause:")
        cause_label.setStyleSheet("color: #9aa4b2; font-size: 11px;")
        layout.addWidget(cause_label)

        conclusion_label = QLabel(_DUMMY_CONCLUSION)
        conclusion_label.setStyleSheet("color: #e3b341; font-weight: 600;")
        conclusion_label.setWordWrap(True)
        layout.addWidget(conclusion_label)

        layout.addStretch(1)

        open_details_button = QPushButton("Open Details")
        layout.addWidget(open_details_button)
