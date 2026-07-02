from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from app.core.issue import Issue
from app.core.risk_level import RiskLevel

_SEVERITY_COLOR = {
    RiskLevel.CRITICAL: "#DC2626",
    RiskLevel.HIGH: "#DC2626",
    RiskLevel.MEDIUM: "#F59E0B",
    RiskLevel.LOW: "#16A34A",
}


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
        name_label.setStyleSheet("font-size: 10px; color: #6B7280;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        step_col.addWidget(name_label)

        row.addLayout(step_col)

        if i < len(steps) - 1:
            arrow = QLabel("→")
            arrow.setStyleSheet("color: #6B7280; font-size: 14px;")
            arrow.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(arrow)

    row.addStretch(1)
    return row


def _issue_steps(issue: Issue) -> list[tuple[str, str, str]]:
    color = _SEVERITY_COLOR.get(issue.severity, "#6B7280")
    evidence_icon = "✓" if issue.evidence else "○"
    cause_icon = "✓" if issue.likely_cause else "○"
    action_icon = "✓" if issue.recommended_actions else "○"
    review_icon = "!" if issue.severity >= RiskLevel.HIGH else "✓"
    return [
        ("Evidence", evidence_icon, "#16A34A" if issue.evidence else "#6B7280"),
        ("Cause", cause_icon, "#16A34A" if issue.likely_cause else "#6B7280"),
        ("Action", action_icon, "#16A34A" if issue.recommended_actions else "#6B7280"),
        ("Risk", review_icon, color),
    ]


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if widget := item.widget():
            widget.deleteLater()
        elif child := item.layout():
            _clear_layout(child)


# Context: agent_reports/2026-07-01_fix-status-summary-report-client-summary.md
class DecisionAssistantWidget(QFrame):
    """Decision Assistant panel populated from Decision Engine issues."""

    def __init__(self) -> None:
        super().__init__()
        self._current_issue: Issue | None = None
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("🤖 Decision Assistant")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self._problem_label = QLabel("Run a scan to get decision guidance.")
        self._problem_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        self._problem_label.setWordWrap(True)
        layout.addWidget(self._problem_label)

        self._steps_layout = QHBoxLayout()
        layout.addLayout(self._steps_layout)

        cause_label = QLabel("Most likely cause:")
        cause_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(cause_label)

        self._conclusion_label = QLabel("No scan result loaded yet.")
        self._conclusion_label.setStyleSheet("color: #6B7280; font-weight: 600;")
        self._conclusion_label.setWordWrap(True)
        layout.addWidget(self._conclusion_label)

        layout.addStretch(1)

        self._open_details_button = QPushButton("Open Details")
        self._open_details_button.clicked.connect(self._open_details)
        self._open_details_button.setEnabled(False)
        layout.addWidget(self._open_details_button)

    def update_data(self, issues: tuple[Issue, ...]) -> None:
        if not issues:
            self._current_issue = None
            self._problem_label.setText("No issues detected.")
            self._conclusion_label.setText("Decision Engine did not find a problem to explain.")
            self._conclusion_label.setStyleSheet("color: #16A34A; font-weight: 600;")
            self._open_details_button.setEnabled(False)
            _clear_layout(self._steps_layout)
            return

        issue = issues[0]
        self._current_issue = issue
        self._problem_label.setText(issue.title)
        conclusion = issue.likely_cause or (
            issue.recommended_actions[0] if issue.recommended_actions else "Review diagnostic evidence."
        )
        color = _SEVERITY_COLOR.get(issue.severity, "#6B7280")
        self._conclusion_label.setText(conclusion)
        self._conclusion_label.setStyleSheet(f"color: {color}; font-weight: 600;")
        self._open_details_button.setEnabled(True)

        _clear_layout(self._steps_layout)
        self._steps_layout.addLayout(_build_step_chain(_issue_steps(issue)))

    def _open_details(self) -> None:
        issue = self._current_issue
        if issue is None:
            return

        evidence = "".join(f"<li>{escape(item)}</li>" for item in issue.evidence) or "<li>No evidence recorded.</li>"
        actions = "".join(
            f"<li>{escape(item)}</li>" for item in issue.recommended_actions
        ) or "<li>Review diagnostic evidence.</li>"
        QMessageBox.information(
            self,
            "Decision details",
            "<b>Problem</b><br>"
            f"{escape(issue.title)}<br><br>"
            "<b>Severity</b><br>"
            f"{escape(issue.severity.name)} ({escape(issue.confidence)} confidence)<br><br>"
            "<b>Evidence</b>"
            f"<ul>{evidence}</ul>"
            "<b>Most likely cause</b><br>"
            f"{escape(issue.likely_cause or 'Unknown')}<br><br>"
            "<b>Suggested next steps</b>"
            f"<ul>{actions}</ul>",
        )
