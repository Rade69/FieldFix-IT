from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.gui.icons import STATUS_CARD_ICONS
from app.gui.styles import TEXT_SECONDARY, secondary_text_style

_COLORS = {
    "ok":       "#16A34A",
    "warning":  "#F59E0B",
    "critical": "#DC2626",
    "neutral":  TEXT_SECONDARY,
}

_DETAIL_ICON = {
    "ok":       ("✓", "#16A34A"),
    "warning":  ("⚠", "#F59E0B"),
    "critical": ("✕", "#DC2626"),
    "neutral":  ("—", TEXT_SECONDARY),
}

_ICON_BG = {
    "Network":       ("#0d3654", "#155f90"),
    "SMB":           ("#1e1254", "#3b2ba0"),
    "Sharing / SMB": ("#1e1254", "#3b2ba0"),
    "Firewall":      ("#3d2000", "#9e5500"),
    "Services":      ("#0d3654", "#155f90"),
    "Printers":      ("#2d1254", "#7b1fa2"),
    "Issues":        ("#3d0d0d", "#9e2222"),
}


class StatusCard(QFrame):
    """Dashboard summary tile — icon, status value, detail line."""

    def __init__(
        self,
        title: str,
        value: str,
        status: str = "neutral",
        detail: str = "",
    ) -> None:
        super().__init__()
        self.setObjectName("StatusCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(140)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(12)

        # Icon circle
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(54, 54)
        icon_path = STATUS_CARD_ICONS.get(title)
        if icon_path:
            self._icon_label.setPixmap(QIcon(str(icon_path)).pixmap(QSize(38, 38)))
        bg, border = _ICON_BG.get(title, ("#0d3654", "#155f90"))
        self._icon_label.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border}; border-radius: 27px;"
        )
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self._icon_label)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(secondary_text_style(size=11, weight=600))
        text_col.addWidget(title_lbl)

        self._value_label = QLabel(value)
        color = _COLORS.get(status, _COLORS["neutral"])
        self._value_label.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {color};"
        )
        text_col.addWidget(self._value_label)

        # Detail row: small icon + text
        self._detail_row = QHBoxLayout()
        self._detail_row.setSpacing(4)
        self._detail_icon = QLabel()
        self._detail_icon.setStyleSheet("font-size: 11px;")
        self._detail_text = QLabel()
        self._detail_text.setStyleSheet(secondary_text_style(size=11))
        self._detail_row.addWidget(self._detail_icon)
        self._detail_row.addWidget(self._detail_text)
        self._detail_row.addStretch(1)
        text_col.addLayout(self._detail_row)

        outer.addLayout(text_col)
        outer.addStretch(1)

        self._set_detail(status, detail)

    def _set_detail(self, status: str, detail: str) -> None:
        icon, color = _DETAIL_ICON.get(status, _DETAIL_ICON["neutral"])
        self._detail_icon.setText(icon)
        self._detail_icon.setStyleSheet(f"font-size: 11px; color: {color};")
        self._detail_text.setText(detail)

    def update(self, value: str, status: str, detail: str = "") -> None:
        color = _COLORS.get(status, _COLORS["neutral"])
        self._value_label.setText(value)
        self._value_label.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {color};"
        )
        self._set_detail(status, detail)
