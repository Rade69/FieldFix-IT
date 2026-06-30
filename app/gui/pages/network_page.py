from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class NetworkPage(QWidget):
    """Placeholder. Real scanning logic arrives in Faza 4 (Network module)."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Network — coming soon"))
        layout.addStretch(1)
