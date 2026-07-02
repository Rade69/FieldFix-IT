import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.core.settings import get_settings
from app.gui.icons import APP_ICON_ICO
from app.gui.main_window import MainWindow
from app.gui.styles import get_stylesheet


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
    app.setStyleSheet(get_stylesheet(get_settings().theme))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
