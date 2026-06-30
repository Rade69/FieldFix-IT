from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from app.gui.widgets.decision_assistant_widget import DecisionAssistantWidget
from app.gui.widgets.issues_widget import IssuesRecommendationsWidget
from app.gui.widgets.quick_actions_widget import QuickActionsWidget
from app.gui.widgets.recent_scan_widget import RecentScanWidget
from app.gui.widgets.status_card import StatusCard
from app.gui.widgets.system_info_widget import SystemInfoWidget
from app.gui.widgets.timeline_widget import ActivityTimelineWidget
from app.gui.widgets.topology_widget import NetworkTopologyWidget

# Dummy data only — replaced by real scan results starting Faza 11 (Dashboard v2).
_DUMMY_CARDS = [
    ("Network", "OK", "ok"),
    ("Sharing / SMB", "OK", "ok"),
    ("Firewall", "WARNING", "warning"),
    ("Services", "OK", "ok"),
    ("Printers", "2", "neutral"),
    ("Issues", "3", "critical"),
]


class DashboardPage(QWidget):
    """Dashboard. All panels show static dummy data — no real scanning yet (see docs/target_gui.md)."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        cards_row = QHBoxLayout()
        for title, value, status in _DUMMY_CARDS:
            cards_row.addWidget(StatusCard(title, value, status))
        layout.addLayout(cards_row)

        info_row = QHBoxLayout()
        info_row.addWidget(SystemInfoWidget())
        info_row.addWidget(RecentScanWidget())

        issues_col = QVBoxLayout()
        issues_col.setSpacing(8)
        issues_col.addWidget(IssuesRecommendationsWidget())
        issues_col.addWidget(QuickActionsWidget())
        info_row.addLayout(issues_col)

        layout.addLayout(info_row)

        layout.addWidget(NetworkTopologyWidget())

        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(8)
        timeline_row.addWidget(ActivityTimelineWidget(), stretch=6)
        timeline_row.addWidget(DecisionAssistantWidget(), stretch=4)
        layout.addLayout(timeline_row)

        layout.addStretch(1)
