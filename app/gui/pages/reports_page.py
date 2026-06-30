from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ReportsPage(QWidget):
    """Placeholder. Report generator arrives in Faza 9."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reports — coming soon"))
        layout.addStretch(1)
