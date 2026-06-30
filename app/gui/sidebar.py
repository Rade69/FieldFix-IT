from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui.icons import NAV_ICONS

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


def _make_item_widget(icon_path, name: str, subtitle: str) -> QWidget:
    """Custom widget for each sidebar row — bypasses Qt's text elide on items."""
    w = QWidget()
    w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    row = QHBoxLayout(w)
    row.setContentsMargins(10, 4, 8, 4)
    row.setSpacing(10)

    icon_lbl = QLabel()
    icon_lbl.setFixedSize(28, 28)
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if icon_path:
        icon_lbl.setPixmap(QIcon(str(icon_path)).pixmap(QSize(26, 26)))
    row.addWidget(icon_lbl)

    text_col = QVBoxLayout()
    text_col.setSpacing(1)
    text_col.setContentsMargins(0, 0, 0, 0)

    name_lbl = QLabel(name)
    name_lbl.setStyleSheet("font-size: 13px; font-weight: 500; background: transparent;")
    text_col.addWidget(name_lbl)

    if subtitle:
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("font-size: 10px; color: #6e7681; background: transparent;")
        text_col.addWidget(sub_lbl)

    row.addLayout(text_col, stretch=1)
    return w


class Sidebar(QListWidget):
    """Left navigation list. Emits page_selected(index) when the user picks a section."""

    page_selected = Signal(int)

    def __init__(self, page_names: list[str]) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(250)
        self.setSpacing(2)

        for name in page_names:
            subtitle = _PAGE_META.get(name, "")
            item = QListWidgetItem(self)
            item.setSizeHint(QSize(240, 58 if subtitle else 46))
            self.addItem(item)
            self.setItemWidget(item, _make_item_widget(NAV_ICONS.get(name), name, subtitle))

        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.page_selected.emit)
