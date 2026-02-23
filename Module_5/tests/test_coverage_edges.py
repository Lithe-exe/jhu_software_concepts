import pytest
import os
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

from board.load_data import clean_date, clean_val, load_data
from board.query_data import DataAnalyzer
from board.clean import DataCleaner
from board.scrape import GradCafeScraper


@pytest.mark.db
def test_load_data_helper_edge_cases():
    """Covers non-string and blank-value branches in loader helper functions."""
    assert clean_val(123) == 123
    assert clean_date(123) == 123
    assert clean_date("   ") is None
    assert clean_date("29 Mar 2024") == "29 Mar 2024"


@pytest.mark.db
def test_load_data_file_not_found_branch():
    """Ensures load_data exits gracefully when the input JSON file is missing."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

    with patch("board.load_data.psycopg.connect", return_value=mock_conn), \
         patch("builtins.open", side_effect=FileNotFoundError):
        load_data("missing.json", reset=False)

    assert mock_cur.execute.called


@pytest.mark.db
def test_get_single_result_handles_psycopg_error():
    """Validates SQL errors are converted into the expected error string."""
    analyzer = DataAnalyzer()
    import board.query_data as qmod

    with patch("board.query_data.psycopg.connect", side_effect=qmod.psycopg.Error("down")):
        result = analyzer._get_single_result("SELECT 1")

    assert "SQL Error" in result


@pytest.mark.db
def test_get_analysis_sets_cq1_na_on_exception():
    """Checks fallback behavior: cq1 is N/A when grouped query fails, cq2 still returns."""
    analyzer = DataAnalyzer()

    with patch.object(DataAnalyzer, "_get_single_result", return_value=1), \
         patch("board.query_data.psycopg.connect", side_effect=Exception("db down")):
        data = analyzer.get_analysis()

    assert data["cq1"] == "N/A"
    assert data["cq2"] == 1


@pytest.mark.web
def test_app_error_and_busy_paths(client):
    """Covers app route branches: query failure, busy gate, and pull-data exception."""
    import app as app_module

    app_module.CACHED_ANALYSIS = None
    with patch("board.query_data.DataAnalyzer.get_analysis", side_effect=Exception("boom")):
        res = client.get("/analysis")
    assert res.status_code == 200

    app_module.IS_BUSY = True
    try:
        busy_res = client.post("/pull-data")
        assert busy_res.status_code == 409
    finally:
        app_module.IS_BUSY = False

    with patch("app.GradCafeScraper") as mock_scraper:
        mock_scraper.return_value.scrape_data.side_effect = RuntimeError("network down")
        err_res = client.post("/pull-data")
    assert err_res.status_code == 500
    assert app_module.IS_BUSY is False


@pytest.mark.web
def test_update_analysis_exception_sets_empty_cache(client):
    """Covers update-analysis exception path that falls back to empty cache."""
    import app as app_module
    app_module.IS_BUSY = False
    app_module.CACHED_ANALYSIS = None

    with patch("board.query_data.DataAnalyzer.get_analysis", side_effect=Exception("db")):
        res = client.post("/update-analysis")

    assert res.status_code == 200
    assert app_module.CACHED_ANALYSIS == {}


@pytest.mark.analysis
def test_cleaner_remaining_branches():
    """Covers cleaner branches for absolute output path, rejected/interview, and null pruning."""
    abs_out = os.path.abspath("out.json")
    cleaner = DataCleaner("raw.json", abs_out)
    assert cleaner.output_file == abs_out
    assert cleaner._clean_str("   ") is None
    assert cleaner._parse_status_date("Interview invite")[0] == "Interview"
    assert "A" not in cleaner._prune_nulls({"A": "   ", "Comments": "ok"})

    result = cleaner.clean_data([{
        "raw_text": "Rejected on 2 Feb GPA: 3.9 GRE: 320 V 160 AW 4.0",
        "raw_prog": "CS",
        "raw_inst": "Uni",
    }])[0]
    assert result["Rejected"] == "2 Feb 2026"
    assert result["GPA"] == 3.9
    assert result["GRE Score"] == 320
    assert result["GRE V Score"] == 160
    assert result["GRE AW"] == 4.0


@pytest.mark.analysis
def test_cleaner_update_and_merge_value_error_return():
    """Covers update_and_merge ValueError branches for existing and incoming JSON reads."""
    cleaner = DataCleaner("raw.json", "out.json")
    with patch("builtins.open", MagicMock()), \
         patch("json.load", side_effect=[ValueError("bad"), ValueError("bad")]), \
         patch.object(cleaner, "save_data") as mock_save:
        cleaner.update_and_merge()
    assert not mock_save.called


@pytest.mark.integration
def test_scraper_init_and_fetch_error_branches():
    """Covers scraper init non-list/failure paths and _fetch_html error/status branches."""
    with patch.object(GradCafeScraper, "_setup_http", return_value=MagicMock()), \
         patch("builtins.open", MagicMock()), \
         patch("json.load", return_value={"not": "a list"}):
        s_non_list = GradCafeScraper(debug=True)
    assert s_non_list.raw_data == []

    with patch.object(GradCafeScraper, "_setup_http", return_value=MagicMock()), \
         patch("builtins.open", MagicMock()), \
         patch("json.load", return_value=[{"raw_date": "1 Jan 2026"}]):
        s_has_date = GradCafeScraper(output_file=os.path.abspath("raw.json"))
    assert s_has_date.latest_stored_date == "1 Jan 2026"

    with patch.object(GradCafeScraper, "_setup_http", return_value=MagicMock()), \
         patch("builtins.open", MagicMock()), \
         patch("json.load", side_effect=ValueError("bad")):
        s_bad_json = GradCafeScraper()
    assert s_bad_json.raw_data == []

    status_scraper = GradCafeScraper(debug=False)
    status_scraper.http = MagicMock()
    status_scraper.http.request.return_value = MagicMock(status=500, data=b"")
    assert status_scraper._fetch_html("http://x") is None

    exc_scraper = GradCafeScraper(debug=True)
    exc_scraper.http = MagicMock()
    exc_scraper.http.request.side_effect = Exception("boom")
    assert exc_scraper._fetch_html("http://x") is None


@pytest.mark.integration
def test_scraper_loop_and_extract_remaining_branches():
    """Covers scrape loop branches and extractor early-return/date-match/save-error cases."""
    s = GradCafeScraper(debug=False)
    s.latest_stored_date = "1 Jan 2026"
    with patch.object(s, "save_raw_data"):
        s.scrape_data(target_count=0, max_pages=10000)

    s2 = GradCafeScraper(debug=False)
    with patch.object(s2, "_fetch_html", side_effect=["<html></html>", "<table><tr><td>School</td><td><span>Prog</span></td><td>2 Jan 2026</td></tr></table>"]), \
         patch.object(s2, "save_raw_data"):
        out = s2.scrape_data(target_count=1, max_pages=2)
    assert len(out) >= 1

    s3 = GradCafeScraper(debug=False)
    s3.latest_stored_date = "3 Jan 2026"
    with patch.object(s3, "_fetch_html", return_value="<table><tr><td>School</td><td><span>Prog</span></td><td>3 Jan 2026</td></tr></table>"), \
         patch.object(s3, "save_raw_data"):
        s3.scrape_data(target_count=5, max_pages=1)

    assert s3._extract_data_from_soup(BeautifulSoup("<html></html>", "html.parser"), "u") == []

    parsed = s3._extract_data_from_soup(
        BeautifulSoup("<table><tr><td>School</td><td><span>Prog</span></td><td>4 Jan 2026</td></tr></table>", "html.parser"),
        "u",
    )
    assert parsed and parsed[0]["raw_date"] == "4 Jan 2026"

    with patch("builtins.open", side_effect=IOError("no write")):
        s3.save_raw_data()


@pytest.mark.db
def test_load_data_handles_psycopg_error_branch():
    """Covers load_data psycopg.Error handler branch."""
    import board.load_data as lmod
    with patch("board.load_data.psycopg.connect", side_effect=lmod.psycopg.Error("db")):
        load_data("x.json")


@pytest.mark.db
def test_load_data_handles_generic_error_branch():
    """Covers load_data generic exception handler branch."""
    with patch("board.load_data.psycopg.connect", side_effect=RuntimeError("boom")):
        load_data("x.json")


@pytest.mark.integration
def test_scrape_data_no_html_continue_branch():
    """Covers scrape_data branch where a fetch returns no HTML and page is skipped."""
    s = GradCafeScraper(debug=False)
    with patch.object(s, "_fetch_html", side_effect=[None, "<table><tr><td>School</td><td><span>Prog</span></td><td>5 Jan 2026</td></tr></table>"]), \
         patch.object(s, "save_raw_data"):
        out = s.scrape_data(target_count=1, max_pages=1)
    assert len(out) >= 1
