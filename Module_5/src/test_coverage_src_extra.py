"""Extra coverage tests needed when running `pytest src/` directly."""

from unittest.mock import patch

from board.clean import DataCleaner
from board.query_data import DataAnalyzer


def test_cleaner_uncovered_branches():
    """Cover remaining helper branches in DataCleaner."""
    # This test intentionally exercises protected helper methods for coverage.
    # pylint: disable=protected-access
    status, parsed = DataCleaner._parse_status_date("Interview on Jan 7")
    assert status == "Interview"
    assert parsed == "7 Jan"

    assert DataCleaner._manual_format_date("2026 12") is None
    assert DataCleaner._manual_format_date("Jan 2026") is None

    assert DataCleaner._extract_origin("American applicant") == "American"
    assert DataCleaner._extract_gre("") == {"total": None, "verbal": None, "aw": None}


def test_query_data_cq1_empty_branch():
    """Cover cq1 empty-result branch in get_analysis()."""

    class _FakeResult:  # pylint: disable=too-few-public-methods
        """This fake object simulates a DB result object with no rows."""

        def fetchall(self):
            """This helper returns no rows to hit the empty-result branch."""
            return []

    class _FakeConn:  # pylint: disable=too-few-public-methods
        """This fake connection models minimal context-manager DB behavior."""

        def __enter__(self):
            """This helper returns the fake connection context."""
            return self

        def __exit__(self, exc_type, exc, tb):
            """This helper preserves exception propagation behavior."""
            return False

        def execute(self, _query, _params):
            """This helper returns an empty fake result set."""
            return _FakeResult()

    analyzer = DataAnalyzer()

    with patch.object(DataAnalyzer, "_get_single_result", return_value="N/A"), patch(
        "board.query_data.psycopg.connect", return_value=_FakeConn()
    ):
        data = analyzer.get_analysis(limit=10)

    assert data["cq1"] == "N/A"
