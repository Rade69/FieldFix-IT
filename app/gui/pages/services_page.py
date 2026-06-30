from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ServicesPage(QWidget):
    """Placeholder. Real scanning logic arrives in Faza 7 (Services module)."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Services — coming soon"))
        layout.addStretch(1)
