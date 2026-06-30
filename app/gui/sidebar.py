from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.gui.icons import UI_ICONS

_PAGE_META = {
    "Dashboard": "",
    "Network": "IP, DNS, adapteri",
    "Sharing / SMB": "Shares, sessions, access",
    "Firewall": "Pravila, profili, zone",
    "Services": "Servisi, startup",
    "Printers": "Štampači, portovi",
    "Topology": "Mrežni uređaji",
    "Fix Center": "Kontrolisani fix",
    "Reports": "Export i istorija",
    "Settings": "Opšte postavke",
    "About": "O aplikaciji",
}


class Sidebar(QListWidget):
    """Left navigation list. Emits page_selected(index) when the user picks a section."""

    page_selected = Signal(int)

    def __init__(self, page_names: list[str]) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(250)
        self.setIconSize(QSize(24, 24))
        self.setSpacing(2)
        for name in page_names:
            subtitle = _PAGE_META.get(name, "")
            text = name
            if subtitle:
                text = f"{text}\n{subtitle}"
            item = QListWidgetItem(QIcon(str(UI_ICONS.get(name, ""))), text, self)
            item.setSizeHint(QSize(220, 52 if subtitle else 44))
        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.page_selected.emit)
