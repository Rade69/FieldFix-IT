from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.gui.icons import APP_ICON_128


def _centered(text: str, style: str = "") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    lbl.setWordWrap(True)
    if style:
        lbl.setStyleSheet(style)
    return lbl


def _separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet("color: #21262d; margin: 4px 0;")
    return sep


class AboutPage(QWidget):
    """About page — application info, creator credits."""

    def __init__(self) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        outer.setContentsMargins(0, 0, 0, 0)

        # Card centred on page
        card = QFrame()
        card.setObjectName("PanelCard")
        card.setFixedWidth(560)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 32, 40, 36)
        layout.setSpacing(10)

        # App icon
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QPixmap(str(APP_ICON_128)))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(icon_lbl)
        layout.addSpacing(4)

        # Title + version
        layout.addWidget(_centered(
            "FieldFix IT",
            "font-size: 22px; font-weight: 800; color: #f0f6fc;",
        ))
        layout.addWidget(_centered(
            "v1.0.0",
            "font-size: 12px; color: #58a6ff;",
        ))
        layout.addWidget(_centered(
            "Windows IT Diagnostics & Repair Tool",
            "color: #9aa4b2; font-size: 13px;",
        ))

        layout.addSpacing(8)
        layout.addWidget(_separator())
        layout.addSpacing(4)

        # Description
        layout.addWidget(_centered(
            "FieldFix IT is a Windows desktop application designed for IT professionals "
            "and power users who need to quickly diagnose and resolve common network, "
            "sharing, firewall, services, and printer issues on Windows 10/11 systems.\n\n"
            "The application operates in Read-Only Scan Mode by default — no system "
            "settings are changed without an explicit confirmation in Fix Center.",
            "color: #6B7280; font-size: 12px; line-height: 1.6;",
        ))

        layout.addSpacing(8)
        layout.addWidget(_separator())
        layout.addSpacing(4)

        # Creator
        layout.addWidget(_centered(
            "Created by",
            "color: #6B7280; font-size: 11px;",
        ))
        layout.addWidget(_centered(
            "Radovan Stojanović",
            "font-size: 15px; font-weight: 700; color: #f0f6fc;",
        ))
        layout.addSpacing(6)
        layout.addWidget(_centered(
            "Built with the assistance of AI coding models",
            "color: #6B7280; font-size: 11px;",
        ))

        ai_row = QHBoxLayout()
        ai_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ai_row.setSpacing(12)
        for name, color in [("Claude Code", "#58a6ff"), ("Codex", "#3fb950")]:
            badge = QLabel(name)
            badge.setStyleSheet(
                f"color: {color}; background: transparent;"
                f"border: 1px solid {color}; border-radius: 4px;"
                f"padding: 3px 12px; font-size: 12px; font-weight: 600;"
            )
            ai_row.addWidget(badge)
        layout.addLayout(ai_row)

        layout.addSpacing(8)
        layout.addWidget(_separator())
        layout.addSpacing(4)

        # Tech stack
        layout.addWidget(_centered(
            "Python 3.11 · PySide6 (Qt6) · PowerShell · Windows 10/11",
            "color: #6B7280; font-size: 11px;",
        ))

        outer.addSpacing(32)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(1)
