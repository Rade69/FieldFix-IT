from enum import Enum


class ScanStatus(Enum):
    """Outcome of a single diagnostic module scan."""

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    NOT_CHECKED = "NOT_CHECKED"

    def __str__(self) -> str:
        return self.value
