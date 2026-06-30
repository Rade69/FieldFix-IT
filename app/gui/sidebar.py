from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class Sidebar(QListWidget):
    """Left navigation list. Emits page_selected(index) when the user picks a section."""

    page_selected = Signal(int)

    def __init__(self, page_names: list[str]) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        for name in page_names:
            QListWidgetItem(name, self)
        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.page_selected.emit)
