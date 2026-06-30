from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.gui.dashboard import DashboardPage
from app.gui.pages.about_page import AboutPage
from app.gui.pages.firewall_page import FirewallPage
from app.gui.pages.fix_center_page import FixCenterPage
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
    ("Fix Center", FixCenterPage),
    ("Reports", ReportsPage),
    ("Settings", SettingsPage),
    ("About", AboutPage),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FieldFix IT — Windows IT Diagnostics & Repair Tool")
        self.setMinimumSize(1120, 700)
        self._fit_to_screen()

        self.pages = QStackedWidget()
        _instances = []
        for _, page_cls in _PAGES:
            inst = page_cls()
            self.pages.addWidget(inst)
            _instances.append(inst)

        self.sidebar = Sidebar([name for name, _ in _PAGES])
        self.sidebar.page_selected.connect(self.pages.setCurrentIndex)

        # Wire Dashboard "Open Fix Center" → navigate to Fix Center page
        _fix_idx = next(i for i, (n, _) in enumerate(_PAGES) if n == "Fix Center")
        _instances[0].open_fix_center.connect(
            lambda: self.pages.setCurrentIndex(_fix_idx)
        )

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.pages, stretch=1)

        self._top_bar = TopBar()
        _instances[0].scan_completed.connect(
            lambda r: self._top_bar.update_network(r.report.network)
        )
        _settings_idx = next(i for i, (n, _) in enumerate(_PAGES) if n == "Settings")
        self._top_bar.open_settings.connect(
            lambda: self.pages.setCurrentIndex(_settings_idx)
        )

        central = QWidget()
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(self._top_bar)
        outer_layout.addWidget(body, stretch=1)
        self.setCentralWidget(central)

        # Scan Mode is always the default — Fix Mode is a manual, later opt-in (see docs/architecture_notes.md).
        self.statusBar().showMessage("Scan Mode: Read Only")

    def _fit_to_screen(self) -> None:
        """Size and center the window within the available screen area (excludes taskbar)."""
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(1360, int(screen.width() * 0.96))
        h = min(860, int(screen.height() * 0.94))
        self.resize(w, h)
        self.move(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2,
        )
