from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.powershell_runner import PowerShellRunner
from app.modules.firewall.models import FirewallData, FirewallRule
from app.modules.firewall.scanner import FirewallScanner

_ACTION_COLOR = {
    "Allow": "#3fb950",
    "Block": "#f85149",
}

_ENABLED_COLOR = {
    True: "#3fb950",
    False: "#9aa4b2",
}

_DEFAULT_INBOUND_COLOR = {
    "Block": "#3fb950",
    "Allow": "#d29922",
}


def _bool_badge(value: bool | None) -> QLabel:
    if value is True:
        text = "✓ On"
        color = _ENABLED_COLOR[True]
    elif value is False:
        text = "✕ Off"
        color = _ENABLED_COLOR[False]
    else:
        text = "- Unknown"
        color = "#9aa4b2"
    label = QLabel(text)
    label.setStyleSheet(f"color: {color}; font-weight: bold;")
    return label


def _action_badge(action: str) -> QLabel:
    color = _ACTION_COLOR.get(action, "#9aa4b2")
    label = QLabel(action or "-")
    label.setStyleSheet(f"color: {color}; font-weight: bold;")
    return label


class FirewallPage(QWidget):
    """Windows Firewall diagnostics page. Shows firewall profiles and rule groups."""

    def __init__(self) -> None:
        super().__init__()
        self._scanner = FirewallScanner(PowerShellRunner())
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("PanelCard")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("🔥 Firewall Diagnostics")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)

        self._status_label = QLabel("Not scanned")
        self._status_label.setStyleSheet("color: #9aa4b2;")
        h_layout.addWidget(self._status_label)
        h_layout.addSpacing(12)

        self._scan_btn = QPushButton("▶ Run Scan")
        self._scan_btn.clicked.connect(self._run_scan)
        h_layout.addWidget(self._scan_btn)

        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._results_widget = QWidget()
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._results_layout.setSpacing(8)
        self._results_layout.setContentsMargins(0, 8, 0, 8)

        placeholder = QLabel("  Click '▶ Run Scan' to check Windows Firewall state.")
        placeholder.setStyleSheet("color: #9aa4b2; padding: 24px;")
        self._results_layout.addWidget(placeholder)

        scroll.setWidget(self._results_widget)
        outer.addWidget(scroll, stretch=1)

    def _run_scan(self) -> None:
        self._scan_btn.setEnabled(False)
        self._status_label.setText("Scanning…")
        self._status_label.setStyleSheet("color: #d29922;")

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        data = self._scanner.scan()
        self._display_results(data)

        self._scan_btn.setEnabled(True)
        self._status_label.setText(f"Done in {data.scan_duration_ms / 1000:.1f}s")
        self._status_label.setStyleSheet("color: #3fb950;")

    def _clear(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _display_results(self, data: FirewallData) -> None:
        self._clear()

        self._results_layout.addWidget(self._profiles_panel(data))
        self._results_layout.addWidget(self._rules_panel(
            "File & Printer Sharing Rules",
            data.file_sharing_rules,
        ))
        self._results_layout.addWidget(self._rules_panel(
            "Network Discovery Rules",
            data.network_discovery_rules,
        ))

        if data.errors:
            self._results_layout.addWidget(self._errors_panel(data.errors))

        self._results_layout.addStretch(1)

    def _profiles_panel(self, data: FirewallData) -> QFrame:
        frame = QFrame()
        frame.setObjectName("PanelCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title = QLabel("Firewall Profiles")
        title.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)

        hdr = QHBoxLayout()
        for text, width in [
            ("Profile", 150),
            ("Enabled", 120),
            ("Default Inbound", 160),
            ("Default Outbound", 160),
        ]:
            label = QLabel(text)
            label.setStyleSheet("color: #9aa4b2; font-size: 11px;")
            label.setFixedWidth(width)
            hdr.addWidget(label)
        hdr.addStretch(1)
        layout.addLayout(hdr)
        layout.addWidget(self._separator())

        by_name = {profile.name: profile for profile in data.profiles}
        for name in ("Domain", "Private", "Public"):
            profile = by_name.get(name)
            row = QHBoxLayout()
            row.setSpacing(0)

            name_label = QLabel(name)
            name_label.setFixedWidth(150)
            name_label.setStyleSheet("font-weight: bold;")
            row.addWidget(name_label)

            row.addWidget(_bool_badge(profile.enabled if profile else None))
            enabled_spacer = QWidget()
            enabled_spacer.setFixedWidth(50)
            row.addWidget(enabled_spacer)

            inbound = profile.default_inbound if profile else ""
            inbound_color = _DEFAULT_INBOUND_COLOR.get(inbound, "#9aa4b2")
            inbound_label = QLabel(inbound or "-")
            inbound_label.setFixedWidth(160)
            inbound_label.setStyleSheet(f"color: {inbound_color}; font-weight: bold;")
            row.addWidget(inbound_label)

            outbound = profile.default_outbound if profile else ""
            outbound_color = (
                "#d29922" if outbound == "Block"
                else "#3fb950" if outbound == "Allow"
                else "#9aa4b2"
            )
            outbound_label = QLabel(outbound or "-")
            outbound_label.setFixedWidth(160)
            outbound_label.setStyleSheet(f"color: {outbound_color};")
            row.addWidget(outbound_label)

            row.addStretch(1)
            layout.addLayout(row)

        return frame

    def _rules_panel(self, title: str, rules: tuple[FirewallRule, ...]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("PanelCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title_label = QLabel(f"{title} ({len(rules)})")
        title_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title_label)

        hdr = QHBoxLayout()
        for text, width in [
            ("Rule", 280),
            ("Direction", 100),
            ("Action", 90),
            ("Enabled", 100),
            ("Profile", 140),
        ]:
            label = QLabel(text)
            label.setStyleSheet("color: #9aa4b2; font-size: 11px;")
            label.setFixedWidth(width)
            hdr.addWidget(label)
        hdr.addStretch(1)
        layout.addLayout(hdr)
        layout.addWidget(self._separator())

        if not rules:
            empty = QLabel("No rules returned by PowerShell.")
            empty.setStyleSheet("color: #9aa4b2; padding: 8px 0;")
            layout.addWidget(empty)
            return frame

        for rule in rules:
            row = QHBoxLayout()
            row.setSpacing(0)

            name_label = QLabel(rule.display_name or rule.name or "-")
            name_label.setFixedWidth(280)
            name_label.setWordWrap(True)
            name_label.setStyleSheet("font-weight: bold;")
            row.addWidget(name_label)

            direction_label = QLabel(rule.direction or "-")
            direction_label.setFixedWidth(100)
            direction_label.setStyleSheet("color: #9aa4b2;")
            row.addWidget(direction_label)

            row.addWidget(_action_badge(rule.action))
            action_spacer = QWidget()
            action_spacer.setFixedWidth(35)
            row.addWidget(action_spacer)

            row.addWidget(_bool_badge(rule.enabled))
            enabled_spacer = QWidget()
            enabled_spacer.setFixedWidth(30)
            row.addWidget(enabled_spacer)

            profile_label = QLabel(rule.profile or "-")
            profile_label.setFixedWidth(140)
            profile_label.setStyleSheet("color: #9aa4b2;")
            row.addWidget(profile_label)

            row.addStretch(1)
            layout.addLayout(row)

        return frame

    def _errors_panel(self, errors: tuple[str, ...]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("PanelCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel(f"⚠ Warnings ({len(errors)})")
        title.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)

        for error in errors:
            label = QLabel(error)
            label.setStyleSheet("color: #d29922;")
            label.setWordWrap(True)
            layout.addWidget(label)

        return frame

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #232a36;")
        return sep
