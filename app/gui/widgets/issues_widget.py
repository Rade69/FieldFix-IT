from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

_ROW_STYLE = (
    "QFrame#IssueRow { border-radius: 6px; padding: 2px; }"
    "QFrame#IssueRow:hover { background-color: #101f2e; }"
)

from app.core.issue import Issue
from app.core.risk_level import RiskLevel

_SEVERITY_COLOR = {
    RiskLevel.CRITICAL: "#f85149",
    RiskLevel.HIGH:     "#f85149",
    RiskLevel.MEDIUM:   "#d29922",
    RiskLevel.LOW:      "#3fb950",
}


def _build_row(color: str, title: str, description: str) -> QFrame:
    wrapper = QFrame()
    wrapper.setObjectName("IssueRow")
    wrapper.setStyleSheet(_ROW_STYLE)

    row = QHBoxLayout(wrapper)
    row.setContentsMargins(4, 4, 4, 4)
    row.setSpacing(8)

    dot = QLabel("●")
    dot.setStyleSheet(f"color: {color}; font-size: 10px;")
    dot.setFixedWidth(14)
    dot.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

    text_col = QVBoxLayout()
    text_col.setSpacing(1)
    t = QLabel(title)
    t.setStyleSheet("font-weight: 600; font-size: 12px;")
    d = QLabel(description)
    d.setStyleSheet("color: #9aa4b2; font-size: 11px;")
    d.setWordWrap(True)
    text_col.addWidget(t)
    text_col.addWidget(d)

    chevron = QLabel("›")
    chevron.setStyleSheet("color: #4b5566; font-size: 16px;")
    chevron.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    row.addWidget(dot)
    row.addLayout(text_col, stretch=1)
    row.addWidget(chevron)
    return wrapper


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if w := item.widget():
            w.deleteLater()
        elif child := item.layout():
            _clear_layout(child)


class IssuesRecommendationsWidget(QFrame):
    """Issues & Recommendations panel. Populated by update_data() after scan."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        header_row = QHBoxLayout()
        self._title_label = QLabel("⚡ Issues & Recommendations (0)")
        self._title_label.setStyleSheet("font-weight: bold; color: #3fb950;")
        header_row.addWidget(self._title_label)
        header_row.addStretch(1)
        view_all = QLabel("View all")
        view_all.setStyleSheet("color: #58a6ff;")
        header_row.addWidget(view_all)
        layout.addLayout(header_row)

        self._content = QVBoxLayout()
        layout.addLayout(self._content)
        self._placeholder()

    def _placeholder(self) -> None:
        lbl = QLabel("Run a scan to detect issues.")
        lbl.setStyleSheet("color: #9aa4b2;")
        self._content.addWidget(lbl)

    def update_data(self, issues: tuple[Issue, ...]) -> None:
        _clear_layout(self._content)
        count = len(issues)
        has_high = any(i.severity >= RiskLevel.HIGH for i in issues)
        color = "#f85149" if has_high else ("#d29922" if count > 0 else "#3fb950")
        self._title_label.setText(f"⚡ Issues & Recommendations ({count})")
        self._title_label.setStyleSheet(f"font-weight: bold; color: {color};")

        if not issues:
            lbl = QLabel("✓ No issues detected.")
            lbl.setStyleSheet("color: #3fb950;")
            self._content.addWidget(lbl)
            return

        for issue in issues[:6]:  # show top 6 in Dashboard panel
            c = _SEVERITY_COLOR.get(issue.severity, "#9aa4b2")
            desc = issue.likely_cause or (issue.evidence[0] if issue.evidence else "")
            self._content.addWidget(_build_row(c, issue.title, desc))
