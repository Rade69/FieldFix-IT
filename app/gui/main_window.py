from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.gui.dashboard import DashboardPage
from app.gui.pages.about_page import AboutPage
from app.gui.pages.firewall_page import FirewallPage
from app.gui.pages.network_page import NetworkPage
from app.gui.pages.printers_page import PrintersPage
from app.gui.pages.reports_page import ReportsPage
from app.gui.pages.services_page import ServicesPage
from app.gui.pages.settings_page import SettingsPage
from app.gui.pages.smb_page import SmbPage
from app.gui.pages.topology_page import TopologyPage
from app.gui.sidebar import Sidebar
from app.gui.top_bar import TopBar

# Order here defines both the sidebar entries and the stacked page order.
_PAGES = [
    ("Dashboard", DashboardPage),
    ("Network", NetworkPage),
    ("Sharing / SMB", SmbPage),
    ("Firewall", FirewallPage),
    ("Services", ServicesPage),
    ("Printers", PrintersPage),
    ("Topology", TopologyPage),
    ("Reports", ReportsPage),
    ("Settings", SettingsPage),
    ("About", AboutPage),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FieldFix IT — Windows IT Diagnostics & Repair Tool")
        self.resize(1280, 800)

        self.pages = QStackedWidget()
        for _, page_cls in _PAGES:
            self.pages.addWidget(page_cls())

        self.sidebar = Sidebar([name for name, _ in _PAGES])
        self.sidebar.page_selected.connect(self.pages.setCurrentIndex)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.pages, stretch=1)

        central = QWidget()
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(TopBar())
        outer_layout.addWidget(body, stretch=1)
        self.setCentralWidget(central)

        # Scan Mode is always the default — Fix Mode is a manual, later opt-in (see docs/architecture_notes.md).
        self.statusBar().showMessage("Scan Mode: Read Only")
