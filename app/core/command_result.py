from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    """Outcome of a single shell command invocation (PowerShell or otherwise).

    PowerShellRunner (Zadatak 3) is the only producer of these — this module
    just defines the shape.
    """

    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: float = 0.0
    timed_out: bool = False
    requires_admin: bool = False
    parsed_json: Any | None = None
    raw_output: str = ""

    @property
    def succeeded(self) -> bool:
        return not self.timed_out and self.exit_code == 0
