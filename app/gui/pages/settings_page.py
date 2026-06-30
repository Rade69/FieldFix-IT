from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    """Placeholder settings page."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Settings — coming soon"))
        layout.addStretch(1)
