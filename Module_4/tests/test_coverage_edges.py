import pytest
from unittest.mock import MagicMock, patch

from board.load_data import clean_date, clean_val, load_data
from board.query_data import DataAnalyzer


@pytest.mark.db
def test_load_data_helper_edge_cases():
    assert clean_val(123) == 123
    assert clean_date(123) == 123
    assert clean_date("   ") is None
    assert clean_date("29 Mar 2024") == "29 Mar 2024"


@pytest.mark.db
def test_load_data_file_not_found_branch():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

    with patch("board.load_data.psycopg.connect", return_value=mock_conn), \
         patch("builtins.open", side_effect=FileNotFoundError):
        load_data("missing.json", reset=False)

    assert mock_cur.execute.called


@pytest.mark.db
def test_get_single_result_handles_psycopg_error():
    analyzer = DataAnalyzer()
    import board.query_data as qmod

    with patch("board.query_data.psycopg.connect", side_effect=qmod.psycopg.Error("down")):
        result = analyzer._get_single_result("SELECT 1")

    assert "SQL Error" in result


@pytest.mark.db
def test_get_analysis_sets_cq1_na_on_exception():
    analyzer = DataAnalyzer()

    with patch.object(DataAnalyzer, "_get_single_result", return_value=1), \
         patch("board.query_data.psycopg.connect", side_effect=Exception("db down")):
        data = analyzer.get_analysis()

    assert data["cq1"] == "N/A"
    assert data["cq2"] == 1
