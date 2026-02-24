"""Extra coverage tests needed when running `pytest src/` directly."""

from unittest.mock import patch

from board.clean import DataCleaner
from board.query_data import DataAnalyzer


def test_cleaner_uncovered_branches():
    """Cover remaining helper branches in DataCleaner."""
    status, parsed = DataCleaner._parse_status_date("Interview on Jan 7")
    assert status == "Interview"
    assert parsed == "7 Jan"

    assert DataCleaner._manual_format_date("2026 12") is None
    assert DataCleaner._manual_format_date("Jan 2026") is None

    assert DataCleaner._extract_origin("American applicant") == "American"
    assert DataCleaner._extract_gre("") == {"total": None, "verbal": None, "aw": None}


def test_query_data_cq1_empty_branch():
    """Cover cq1 empty-result branch in get_analysis()."""

    class _FakeResult:
        def fetchall(self):
            return []

    class _FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, _query, _params):
            return _FakeResult()

    analyzer = DataAnalyzer()

    with patch.object(DataAnalyzer, "_get_single_result", return_value="N/A"), patch(
        "board.query_data.psycopg.connect", return_value=_FakeConn()
    ):
        data = analyzer.get_analysis(limit=10)

    assert data["cq1"] == "N/A"
