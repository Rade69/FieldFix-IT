from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class FirewallPage(QWidget):
    """Placeholder. Real scanning logic arrives in Faza 6 (Firewall module)."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Firewall — coming soon"))
        layout.addStretch(1)
