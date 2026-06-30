"""Isolated legacy text parser for 'net view' output.

'net view' is a legacy command with no JSON equivalent — its output is parsed
here and nowhere else. See docs/architecture_notes.md (PowerShell: JSON prvo).
"""

import re

from app.modules.smb.models import NetViewEntry

_ERROR_RE = re.compile(r"System error (\d+) has occurred", re.IGNORECASE)
# "Used as" column contains a drive-letter mapping (e.g. "Z:") when present
_DRIVE_LETTER_RE = re.compile(r"^[A-Za-z]:$")


def parse_error_code(output: str) -> int | None:
    """Extract Windows error code from 'net view' stdout (e.g. 'System error 53')."""
    m = _ERROR_RE.search(output)
    return int(m.group(1)) if m else None


def parse_shares(output: str) -> list[NetViewEntry]:
    """Parse share rows from 'net view \\\\IP' stdout.

    Expected format after the separator line:
        ShareName   Disk   [Used as]   [Comment]
    Stops at 'The command completed successfully.' or end of output.
    """
    entries: list[NetViewEntry] = []
    past_separator = False

    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^-{10,}", stripped):
            past_separator = True
            continue
        if not past_separator:
            continue
        if stripped.lower().startswith("the command completed"):
            break

        parts = stripped.split()
        if not parts:
            continue
        name = parts[0]
        share_type = parts[1] if len(parts) > 1 else ""
        # "Used as" column is a drive-letter mapping (e.g. "Z:") when filled.
        # When empty, comment starts at index 2; when filled, it starts at index 3.
        if len(parts) > 2 and _DRIVE_LETTER_RE.match(parts[2]):
            comment = " ".join(parts[3:])
        else:
            comment = " ".join(parts[2:]) if len(parts) > 2 else ""
        entries.append(NetViewEntry(name=name, share_type=share_type, comment=comment))

    return entries
