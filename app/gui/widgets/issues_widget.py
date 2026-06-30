from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

# Dummy data only — replaced by real Issue objects once Decision Engine exists (Faza 10).
_DUMMY_ISSUES = [
    ("#f85149", "File and Printer Sharing (Inbound)", "Firewall pravilo je isključeno."),
    ("#f85149", "Network Discovery (Inbound)", "Firewall pravilo je isključeno."),
    ("#d29922", "SMB1 is Disabled", "Preporuka: ostaviti isključeno (bezbjednost)."),
]


def _build_row(color: str, title: str, description: str) -> QHBoxLayout:
    row = QHBoxLayout()
    dot = QLabel("●")
    dot.setStyleSheet(f"color: {color};")
    dot.setAlignment(Qt.AlignmentFlag.AlignTop)

    text_column = QVBoxLayout()
    text_column.setSpacing(2)
    title_label = QLabel(title)
    title_label.setStyleSheet("font-weight: bold;")
    desc_label = QLabel(description)
    desc_label.setStyleSheet("color: #9aa4b2;")
    desc_label.setWordWrap(True)
    text_column.addWidget(title_label)
    text_column.addWidget(desc_label)

    row.addWidget(dot)
    row.addLayout(text_column)
    return row


class IssuesRecommendationsWidget(QFrame):
    """Issues & Recommendations panel. Dummy issues — replaced by real Issue objects (Faza 10)."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        header_row = QHBoxLayout()
        title = QLabel(f"⚡ Issues & Recommendations ({len(_DUMMY_ISSUES)})")
        title.setStyleSheet("font-weight: bold; color: #f85149;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        view_all = QLabel("View all")
        view_all.setStyleSheet("color: #58a6ff;")
        header_row.addWidget(view_all)
        layout.addLayout(header_row)

        for color, title_text, description in _DUMMY_ISSUES:
            layout.addLayout(_build_row(color, title_text, description))
