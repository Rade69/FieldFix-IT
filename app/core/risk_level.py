from enum import IntEnum


class RiskLevel(IntEnum):
    """Risk level for a recommendation/fix action.

    IntEnum gives natural ordering (LOW < MEDIUM < HIGH < CRITICAL) so
    callers can do e.g. `if level >= RiskLevel.HIGH`.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __str__(self) -> str:
        return self.name
