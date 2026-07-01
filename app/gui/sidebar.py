from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.gui.icons import NAV_ICONS

_PAGE_META = {
    "Dashboard": "",
    "Network": "IP, DNS, adapters",
    "Sharing / SMB": "Shares, sessions, access",
    "Firewall": "Rules, profiles, zones",
    "Services": "Services, startup",
    "Printers": "Printers, ports",
    "Topology": "Network devices",
    "Fix Center": "Controlled fixes",
    "Reports": "Export and history",
    "Settings": "General settings",
    "About": "About this app",
}


class Sidebar(QListWidget):
    """Left navigation list. Emits page_selected(index) when the user picks a section."""

    page_selected = Signal(int)

    def __init__(self, page_names: list[str]) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(250)
        self.setIconSize(QSize(30, 30))
        self.setSpacing(2)
        # ElideNone prevents "..." only when text fits on one line.
        # Subtitles are shown as tooltips to avoid multi-line truncation.
        self.setTextElideMode(Qt.TextElideMode.ElideNone)

        for name in page_names:
            icon = QIcon(str(NAV_ICONS.get(name, "")))
            item = QListWidgetItem(icon, name, self)
            item.setSizeHint(QSize(240, 48))
            subtitle = _PAGE_META.get(name, "")
            if subtitle:
                item.setToolTip(subtitle)

        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.page_selected.emit)
