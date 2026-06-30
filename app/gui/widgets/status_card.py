from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatusCard(QFrame):
    """Dashboard summary tile. Displays dummy/static values in this phase — no live scan data yet."""

    _COLORS = {
        "ok": "#2ecc71",
        "warning": "#f1c40f",
        "critical": "#e74c3c",
        "neutral": "#cccccc",
    }

    def __init__(self, title: str, value: str, status: str = "neutral") -> None:
        super().__init__()
        self.setObjectName("StatusCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 11px;")

        value_label = QLabel(value)
        color = self._COLORS.get(status, self._COLORS["neutral"])
        value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")

        self._value_label = value_label
        layout.addWidget(title_label)
        layout.addWidget(value_label)

    def update(self, value: str, status: str) -> None:
        color = self._COLORS.get(status, self._COLORS["neutral"])
        self._value_label.setText(value)
        self._value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
