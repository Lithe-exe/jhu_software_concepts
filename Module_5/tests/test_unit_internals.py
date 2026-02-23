import pytest
import sys
from unittest.mock import MagicMock, patch

# Direct imports
from board.clean import DataCleaner
from board.scrape import GradCafeScraper
from board.load_data import clean_date, clean_val, load_data

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
    
    # Regex Fix Test
    gre = c._extract_gre(txt)
    assert gre['total'] == 160
    assert gre['verbal'] == 155
    assert gre['aw'] == 4.5