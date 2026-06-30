from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class RiskBadge(QLabel):
    """Visual risk-level indicator (LOW/MEDIUM/HIGH/CRITICAL).

    This is display-only for now: set_level() just changes color/text.
    Real risk evaluation logic belongs to Recommendation/RiskLevel models (Faza 2+),
    not to this widget.
    """

    _COLORS = {
        "LOW": "#2ecc71",
        "MEDIUM": "#f1c40f",
        "HIGH": "#e67e22",
        "CRITICAL": "#e74c3c",
    }

    def __init__(self, level: str = "LOW") -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_level(level)

    def set_level(self, level: str) -> None:
        level = level.upper()
        color = self._COLORS.get(level, "#888888")
        self.setText(level)
        self.setStyleSheet(
            f"background-color: {color}; color: white; font-weight: bold; "
            f"border-radius: 4px; padding: 2px 8px;"
        )
