from app.core.scan_status import ScanStatus


def test_values():
    assert ScanStatus.OK.value == "OK"
    assert ScanStatus.NOT_CHECKED.value == "NOT_CHECKED"


def test_str():
    assert str(ScanStatus.WARNING) == "WARNING"
