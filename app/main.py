import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.gui.icons import APP_ICON_ICO
from app.gui.main_window import MainWindow
from app.gui.theme import DARK_STYLESHEET


def _set_windows_app_id() -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "FieldFixIT.Diagnostics"
        )
    except Exception:
        pass


def main() -> None:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("FieldFix IT")
    app.setWindowIcon(QIcon(str(APP_ICON_ICO)))
    app.setStyleSheet(DARK_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
