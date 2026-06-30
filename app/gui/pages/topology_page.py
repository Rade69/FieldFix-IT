from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TopologyPage(QWidget):
    """Placeholder. Topology engine arrives in Faza 12 — not part of the MVP skeleton."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Topology — coming soon"))
        layout.addStretch(1)
