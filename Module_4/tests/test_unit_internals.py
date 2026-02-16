import pytest
import sys
import json
from unittest.mock import MagicMock, patch, mock_open

# Import modules directly (since src is in path)
from src.board.clean import DataCleaner
from src.board.scrape import GradCafeScraper
from src.board.load_data import clean_date, clean_val, load_data
from src.board.query_data import DataAnalyzer

# --- 1. CLEANER LOGIC TESTS ---
@pytest.mark.db
def test_cleaner_internals():
    # Test Path Resolution
    c = DataCleaner("raw.json", "clean.json")
    assert "src" in c.input_file or "board" in c.input_file

    # Test Date Parsing logic
    s, d = c._parse_status_date("Accepted on 15 Feb")
    assert s == "Accepted" and d == "15 Feb"
    s, d = c._parse_status_date("Wait listed")
    assert s == "Waitlisted" and d is None

    # Test Manual Date Formatting
    assert c._manual_format_date("14 Feb 2026") == "14 Feb 2026"
    assert c._manual_format_date("Jan 1, 2025") == "1 Jan 2025"
    assert c._manual_format_date(None) is None

    # Test Regex Extractors
    txt = "GPA: 3.8 GRE: 160 V 155 AW 4.5 Fall 2026 International"
    assert c._extract_gpa(txt) == 3.8
    assert c._extract_season(txt) == "Fall 2026"
    assert c._extract_origin(txt) == "International"
    gre = c._extract_gre(txt)
    assert gre['total'] == 160

    # Test Helpers
    assert c._clean_str("  hi  ") == "hi"
    assert c._clean_str(None) is None
    
    # Test Null Pruning
    obj = {"A": None, "B": "val", "Comments": None}
    res = c._prune_nulls(obj)
    assert "A" not in res
    assert res["Comments"] == ""

    # Test Missing File Handling
    with patch("builtins.open", side_effect=FileNotFoundError):
        c.update_and_merge()
        assert len(c.cleaned_data) == 0

# --- 2. SCRAPER LOGIC TESTS ---
@pytest.mark.db
def test_scraper_internals():
    s = GradCafeScraper("dummy.json", debug=True)

    # Test HTTP Error Handling (500)
    mock_resp = MagicMock()
    mock_resp.status = 500
    s.http.request = MagicMock(return_value=mock_resp)
    assert s._fetch_html("http://bad.url") is None

    # Test Exception Handling
    s.http.request.side_effect = Exception("Timeout")
    assert s._fetch_html("http://bad.url") is None

    # Test Resume Logic (Loading existing raw data)
    with patch("builtins.open", mock_open(read_data='[{"raw_date": "1 Jan"}]')):
        s2 = GradCafeScraper("dummy.json")
        assert s2.latest_stored_date == "1 Jan"

@pytest.mark.db
def test_scraper_parsing_loop():
    """Test the actual HTML parsing loop in scrape_data."""
    s = GradCafeScraper("dummy.json")
    
    # Valid HTML to trigger parsing logic
    html = """
    <html><table>
      <tr>
         <td>Test Uni</td>
         <td><span>CS</span><span>PhD</span></td>
         <td>Accepted on 1 Jan 2026</td>
         <td><p>Comments</p></td>
      </tr>
    </table></html>
    """
    
    # Mock _fetch_html to return our HTML
    with patch.object(s, '_fetch_html', return_value=html):
        # Mock save_raw_data so we don't write to disk
        with patch.object(s, 'save_raw_data'):
            data = s.scrape_data(max_pages=1)
            assert len(data) > 0
            assert data[0]['raw_inst'] == "Test Uni"

# --- 3. LOADER & QUERY TESTS ---
@pytest.mark.db
def test_loader_internals():
    # Test Leap Year & Null logic
    assert clean_date("29 Feb 2024") == "29 Feb 2024"
    assert clean_date("29 Feb 2023") is None
    assert clean_val("Te\x00st") == "Test"

    # Test DB Connection Failure
    mock_psycopg = sys.modules['psycopg']
    mock_psycopg.connect.side_effect = mock_psycopg.Error("DB Down")
    # Should print error, not crash
    load_data("dummy.json")
    mock_psycopg.connect.side_effect = None

@pytest.mark.analysis
def test_query_errors():
    analyzer = DataAnalyzer()
    mock_psycopg = sys.modules['psycopg']
    
    # Test SQL Error inside _get_single_result
    mock_psycopg.connect.side_effect = mock_psycopg.Error("SQL Fail")
    res = analyzer._get_single_result("SELECT 1")
    assert "SQL Error" in str(res)
    
    # Test General Exception inside get_analysis (CQ1 coverage)
    mock_psycopg.connect.side_effect = Exception("General Fail")
    with patch.object(analyzer, '_get_single_result', return_value=0):
        data = analyzer.get_analysis()
        assert data['cq1'] == "N/A"
    
    mock_psycopg.connect.side_effect = None