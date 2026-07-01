from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.gui.dashboard import DashboardPage
from app.gui.icons import APP_ICON_ICO
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
        self.setWindowIcon(QIcon(str(APP_ICON_ICO)))
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

        # Wire Dashboard signals → navigate to correct page (also sync sidebar)
        def _go(idx: int) -> None:
            self.pages.setCurrentIndex(idx)
            self.sidebar.setCurrentRow(idx)

        _fix_idx = next(i for i, (n, _) in enumerate(_PAGES) if n == "Fix Center")
        _instances[0].open_fix_center.connect(lambda: _go(_fix_idx))

        _topo_idx = next(i for i, (n, _) in enumerate(_PAGES) if n == "Topology")
        _instances[0].open_topology.connect(lambda: _go(_topo_idx))

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.pages, stretch=1)

        self._top_bar = TopBar()
        def _push_scan(r) -> None:
            ts = r.scanned_at
            net = r.report.network
            prn = r.report.printers
            smb = r.report.smb
            svc = r.report.services
            if net:
                _instances[_idx("Network")].load_data(net, ts)
            if prn:
                _instances[_idx("Printers")].load_data(prn, ts)
            if smb:
                _instances[_idx("Sharing / SMB")].load_data(smb, ts)
            if svc:
                _instances[_idx("Services")].load_data(svc, ts)
            if net and prn:
                _instances[_idx("Topology")].load_data(net, prn, ts)
            _instances[_idx("Reports")].set_last_result(r)
            self._top_bar.update_network(net)

        def _idx(name: str) -> int:
            return next(i for i, (n, _) in enumerate(_PAGES) if n == name)

        _instances[0].scan_completed.connect(_push_scan)
        _settings_idx = next(i for i, (n, _) in enumerate(_PAGES) if n == "Settings")
        self._top_bar.open_settings.connect(lambda: _go(_settings_idx))

        _dash_idx = next(i for i, (n, _) in enumerate(_PAGES) if n == "Dashboard")
        _dashboard = _instances[_dash_idx]
        self._top_bar.start_scan.connect(lambda: (_go(_dash_idx), _dashboard.run_scan()))

        central = QWidget()
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(self._top_bar)
        outer_layout.addWidget(body, stretch=1)
        self.setCentralWidget(central)

        self._setup_status_bar()

    def _setup_status_bar(self) -> None:
        bar = self.statusBar()
        # Scan Mode is always default — Fix Mode is a manual opt-in (see docs/architecture_notes.md)
        mode_lbl = QLabel("🛡 Scan Mode: Read Only")
        mode_lbl.setStyleSheet("color: #3fb950; font-weight: 600; padding: 0 8px;")
        bar.addWidget(mode_lbl)

        self._sb_status = QLabel("● Ready")
        self._sb_status.setStyleSheet("color: #9aa4b2; padding: 0 8px;")
        bar.addWidget(self._sb_status)

        export_btn = QPushButton("📄 Export Report")
        export_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #58a6ff; border: none;"
            " padding: 2px 8px; font-size: 12px; }"
            "QPushButton:hover { color: #f0f6fc; }"
        )
        bar.addPermanentWidget(export_btn)

        last_report_btn = QPushButton("📋 Open Last Report")
        last_report_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #58a6ff; border: none;"
            " padding: 2px 8px; font-size: 12px; }"
            "QPushButton:hover { color: #f0f6fc; }"
        )
        bar.addPermanentWidget(last_report_btn)

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
