"""Settings page — Scanning / Reports / Safety preferences."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.settings import AppSettings, get_settings
from app.gui.theme import get_stylesheet, normalize_theme


def _section(title: str) -> tuple[QGroupBox, QVBoxLayout]:
    box = QGroupBox(title)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(16, 12, 16, 14)
    layout.setSpacing(10)
    return box, layout


def _label(text: str, muted: bool = False) -> QLabel:
    lbl = QLabel(text)
    if muted:
        lbl.setStyleSheet("color: #6B7280; font-size: 11px;")
    return lbl


def _row(left: QWidget, right: QWidget | None = None) -> QHBoxLayout:
    r = QHBoxLayout()
    r.setContentsMargins(0, 0, 0, 0)
    r.addWidget(left, stretch=1)
    if right:
        r.addWidget(right)
    return r


class SettingsPage(QWidget):
    """User-facing preferences: Scanning, Reports, Safety."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = get_settings()
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("PanelCard")
        header.setStyleSheet(
            "QFrame#PanelCard { border-radius: 0; border-left: none;"
            " border-right: none; border-top: none; }"
        )
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(16, 10, 16, 10)
        title = QLabel("⚙ Settings")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_row.addWidget(title)
        h_row.addStretch(1)

        self._saved_lbl = QLabel("")
        self._saved_lbl.setStyleSheet("color: #3fb950; font-size: 12px;")
        h_row.addWidget(self._saved_lbl)

        reset_btn = QPushButton("Reset to defaults")
        reset_btn.setObjectName("SecondaryButton")
        reset_btn.clicked.connect(self._reset_defaults)
        h_row.addWidget(reset_btn)
        outer.addWidget(header)

        # ── Scroll area ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self._build_appearance())
        layout.addWidget(self._build_scanning())
        layout.addWidget(self._build_reports())
        layout.addWidget(self._build_safety())

        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

    # ── Section: Appearance ──────────────────────────────────────────────────

    def _build_appearance(self) -> QGroupBox:
        box, layout = _section("Appearance")

        theme_row = QHBoxLayout()
        theme_row.addWidget(_label("Application theme:"), stretch=1)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        theme_map = {"dark": 0, "light": 1}
        self._theme_combo.setCurrentIndex(theme_map.get(normalize_theme(self._settings.theme), 0))
        self._theme_combo.setFixedWidth(130)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self._theme_combo)
        layout.addLayout(theme_row)

        layout.addWidget(_label(
            "Theme changes apply immediately and are saved for the next launch.",
            muted=True,
        ))

        return box

    # ── Section: Scanning ─────────────────────────────────────────────────────

    def _build_scanning(self) -> QGroupBox:
        box, layout = _section("Scanning")

        layout.addWidget(_label("Modules included in default scan:"))

        self._cb_network  = self._checkbox("Network", self._settings.scan_network,
                                           lambda v: self._set("scan_network", v))
        self._cb_smb      = self._checkbox("Sharing / SMB", self._settings.scan_smb,
                                           lambda v: self._set("scan_smb", v))
        self._cb_services = self._checkbox("Services", self._settings.scan_services,
                                           lambda v: self._set("scan_services", v))
        self._cb_printers = self._checkbox("Printers", self._settings.scan_printers,
                                           lambda v: self._set("scan_printers", v))

        for cb in (self._cb_network, self._cb_smb, self._cb_services, self._cb_printers):
            layout.addWidget(cb)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #21262d;")
        layout.addWidget(sep)

        # Timeout
        timeout_row = QHBoxLayout()
        timeout_row.addWidget(_label("Scan timeout per module (seconds):"), stretch=1)
        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(10, 120)
        self._timeout_spin.setValue(self._settings.scan_timeout_sec)
        self._timeout_spin.setSuffix(" s")
        self._timeout_spin.setFixedWidth(80)
        self._timeout_spin.valueChanged.connect(lambda v: self._set("scan_timeout_sec", v))
        timeout_row.addWidget(self._timeout_spin)
        layout.addLayout(timeout_row)

        # Max topology devices
        topo_row = QHBoxLayout()
        topo_row.addWidget(_label("Max devices shown in topology:"), stretch=1)
        self._topo_spin = QSpinBox()
        self._topo_spin.setRange(4, 32)
        self._topo_spin.setValue(self._settings.max_topology_devices)
        self._topo_spin.setFixedWidth(80)
        self._topo_spin.valueChanged.connect(lambda v: self._set("max_topology_devices", v))
        topo_row.addWidget(self._topo_spin)
        layout.addLayout(topo_row)

        # Auto-scan on startup
        self._cb_autoscan = self._checkbox(
            "Auto-scan on startup",
            self._settings.auto_scan_on_startup,
            lambda v: self._set("auto_scan_on_startup", v),
        )
        layout.addWidget(self._cb_autoscan)

        return box

    # ── Section: Reports ──────────────────────────────────────────────────────

    def _build_reports(self) -> QGroupBox:
        box, layout = _section("Reports")

        # Save directory
        layout.addWidget(_label("Save reports to:"))
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit(self._settings.reports_dir)
        self._dir_edit.setReadOnly(True)
        dir_row.addWidget(self._dir_edit, stretch=1)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        # Format
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(_label("Report format:"), stretch=1)
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["HTML", "Markdown", "JSON"])
        fmt_map = {"html": 0, "markdown": 1, "json": 2}
        self._fmt_combo.setCurrentIndex(fmt_map.get(self._settings.reports_format, 0))
        self._fmt_combo.setFixedWidth(110)
        self._fmt_combo.currentIndexChanged.connect(self._on_format_changed)
        fmt_row.addWidget(self._fmt_combo)
        layout.addLayout(fmt_row)

        # Auto-open
        self._cb_autoopen = self._checkbox(
            "Open report automatically after scan",
            self._settings.auto_open_report,
            lambda v: self._set("auto_open_report", v),
        )
        layout.addWidget(self._cb_autoopen)

        return box

    # ── Section: Safety ───────────────────────────────────────────────────────

    def _build_safety(self) -> QGroupBox:
        box, layout = _section("Safety")

        # Scan mode info
        mode_frame = QFrame()
        mode_frame.setObjectName("SafetyFrame")
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(12, 8, 12, 8)
        mode_layout.addWidget(_label("🛡  Default mode:"))
        mode_val = QLabel("Scan Mode (Read Only)")
        mode_val.setStyleSheet("color: #16A34A; font-weight: bold;")
        mode_layout.addWidget(mode_val)
        mode_layout.addStretch(1)
        layout.addWidget(mode_frame)
        layout.addWidget(_label(
            "Fix Mode is activated per action in Fix Center — never globally.",
            muted=True,
        ))

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #21262d;")
        layout.addWidget(sep)

        # Confirm before apply — read-only
        confirm_frame = QFrame()
        confirm_layout = QHBoxLayout(confirm_frame)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(8)
        lock = QLabel("🔒")
        confirm_layout.addWidget(lock)
        confirm_lbl = QLabel("Confirm before applying any fix")
        confirm_layout.addWidget(confirm_lbl, stretch=1)
        always_lbl = QLabel("Always ON")
        always_lbl.setObjectName("SuccessBadge")
        confirm_layout.addWidget(always_lbl)
        layout.addWidget(confirm_frame)
        layout.addWidget(_label(
            "This setting cannot be disabled. Every fix requires explicit user confirmation.",
            muted=True,
        ))

        return box

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _checkbox(self, text: str, checked: bool, on_change) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.toggled.connect(on_change)
        return cb

    def _set(self, key: str, value) -> None:
        setattr(self._settings, key, value)
        self._settings.save()
        self._saved_lbl.setText("✓ Saved")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._saved_lbl.setText(""))

    def _browse_dir(self) -> None:
        current = self._settings.reports_dir or str(Path.home() / "Desktop")
        chosen = QFileDialog.getExistingDirectory(self, "Select reports folder", current)
        if chosen:
            self._dir_edit.setText(chosen)
            self._set("reports_dir", chosen)

    def _on_format_changed(self, idx: int) -> None:
        fmt = ["html", "markdown", "json"][idx]
        self._set("reports_format", fmt)

    def _on_theme_changed(self, idx: int) -> None:
        theme = ["dark", "light"][idx]
        self._set("theme", theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_stylesheet(theme))

    def _reset_defaults(self) -> None:
        defaults = AppSettings()
        self._settings.__dict__.update(defaults.__dict__)
        self._settings.save()
        # Refresh widgets
        self._cb_network.setChecked(defaults.scan_network)
        self._cb_smb.setChecked(defaults.scan_smb)
        self._cb_services.setChecked(defaults.scan_services)
        self._cb_printers.setChecked(defaults.scan_printers)
        self._timeout_spin.setValue(defaults.scan_timeout_sec)
        self._topo_spin.setValue(defaults.max_topology_devices)
        self._cb_autoscan.setChecked(defaults.auto_scan_on_startup)
        self._theme_combo.setCurrentIndex(0)
        self._dir_edit.setText(defaults.reports_dir)
        self._fmt_combo.setCurrentIndex(0)
        self._cb_autoopen.setChecked(defaults.auto_open_report)
        self._saved_lbl.setText("✓ Reset to defaults")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._saved_lbl.setText(""))
