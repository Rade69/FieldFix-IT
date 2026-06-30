from app.modules.smb.net_view_parser import parse_error_code, parse_shares

_NET_VIEW_SUCCESS = """\
Shared resources at \\\\192.168.1.100

Share name  Type  Used as  Comment

-------------------------------------------------------------------------------
docs        Disk
photos      Disk           Family photos
ADMIN$      Disk           Remote Admin
The command completed successfully.
"""

_NET_VIEW_ERROR_53 = """\
System error 53 has occurred.

The network path was not found.
"""

_NET_VIEW_ERROR_1272 = """\
System error 1272 has occurred.

You can't access this shared folder because your organization's security policies\
 block unauthenticated guest access.
"""

_NET_VIEW_EMPTY_TABLE = """\
Shared resources at \\\\192.168.1.200

Share name  Type  Used as  Comment

-------------------------------------------------------------------------------
The command completed successfully.
"""


class TestParseErrorCode:
    def test_detects_error_53(self):
        assert parse_error_code(_NET_VIEW_ERROR_53) == 53

    def test_detects_error_1272(self):
        assert parse_error_code(_NET_VIEW_ERROR_1272) == 1272

    def test_no_error_returns_none(self):
        assert parse_error_code(_NET_VIEW_SUCCESS) is None

    def test_empty_string_returns_none(self):
        assert parse_error_code("") is None


class TestParseShares:
    def test_parses_three_shares(self):
        entries = parse_shares(_NET_VIEW_SUCCESS)
        assert len(entries) == 3

    def test_first_share_name(self):
        entries = parse_shares(_NET_VIEW_SUCCESS)
        assert entries[0].name == "docs"
        assert entries[0].share_type == "Disk"

    def test_share_with_comment(self):
        entries = parse_shares(_NET_VIEW_SUCCESS)
        photo = next(e for e in entries if e.name == "photos")
        assert photo.comment == "Family photos"

    def test_admin_share_parsed(self):
        entries = parse_shares(_NET_VIEW_SUCCESS)
        names = [e.name for e in entries]
        assert "ADMIN$" in names

    def test_empty_table_returns_empty_list(self):
        assert parse_shares(_NET_VIEW_EMPTY_TABLE) == []

    def test_error_output_returns_empty_list(self):
        assert parse_shares(_NET_VIEW_ERROR_53) == []
