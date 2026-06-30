from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.gui.icons import APP_ICON_128


class AboutPage(QWidget):
    """Static About page."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        layout.addSpacing(24)

        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(str(APP_ICON_128)))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(icon_label)

        title = QLabel("FieldFix IT v0.1.0 (skeleton)")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title)

        subtitle = QLabel("Windows IT Diagnostics & Repair Tool")
        subtitle.setStyleSheet("color: #9aa4b2;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(subtitle)

        layout.addStretch(1)
