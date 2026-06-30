from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SmbPage(QWidget):
    """Placeholder. Real scanning logic arrives in Faza 5 (SMB module)."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sharing / SMB — coming soon"))
        layout.addStretch(1)
