from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PrintersPage(QWidget):
    """Placeholder. Real scanning logic arrives in Faza 8 (Printer module)."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Printers — coming soon"))
        layout.addStretch(1)
