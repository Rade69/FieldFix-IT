"""Smoke test: the GUI shell builds without a running event loop."""

import pytest
from PySide6.QtWidgets import QApplication

from app.gui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp_instance():
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_builds(qapp_instance):
    window = MainWindow()
    assert window.windowTitle().startswith("FieldFix IT")
    assert window.sidebar.count() == window.pages.count()


def test_dashboard_is_first_page(qapp_instance):
    window = MainWindow()
    assert window.pages.currentIndex() == 0
