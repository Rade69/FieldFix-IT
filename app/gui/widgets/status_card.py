from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.gui.icons import UI_ICONS


class StatusCard(QFrame):
    """Dashboard summary tile. Displays dummy/static values in this phase — no live scan data yet."""

    _COLORS = {
        "ok": "#00d26a",
        "warning": "#f5b301",
        "critical": "#ff4d4f",
        "neutral": "#9aa4b2",
    }

    def __init__(self, title: str, value: str, status: str = "neutral") -> None:
        super().__init__()
        self.setObjectName("StatusCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(42, 42)
        icon_path = UI_ICONS.get(title)
        if icon_path:
            self._icon_label.setPixmap(QIcon(str(icon_path)).pixmap(QSize(24, 24)))
        self._icon_label.setStyleSheet(
            "background-color: #0d3654; border: 1px solid #155f90; "
            "border-radius: 21px;"
        )
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #f0f6fc; font-size: 12px; font-weight: 700;")

        value_label = QLabel(value)
        color = self._COLORS.get(status, self._COLORS["neutral"])
        value_label.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color};")

        self._value_label = value_label
        text_col.addWidget(title_label)
        text_col.addWidget(value_label)
        layout.addLayout(text_col)
        layout.addStretch(1)

    def update(self, value: str, status: str) -> None:
        color = self._COLORS.get(status, self._COLORS["neutral"])
        self._value_label.setText(value)
        self._value_label.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color};")
