import pytest
from unittest.mock import patch, mock_open
from src.board.load_data import clean_date, load_data

@pytest.mark.db
def test_clean_date_leap_and_invalid_year():
    # non-leap year: triggers "return None" path
    assert clean_date("29 Feb 2025") is None

    # leap year: should pass through and return string
    assert clean_date("29 Feb 2024") == "29 Feb 2024"

    # invalid year: triggers ValueError branch (your missing line 43)
    assert clean_date("29 Feb xxxx") is None


@pytest.mark.db
def test_load_data_reset_false_branch_hits_ready():
    # Make sure file read succeeds so we reach "Table 'applicants' ready."
    with patch("builtins.open", mock_open(read_data="[]")), patch("json.load", return_value=[]):
        load_data("dummy.json", reset=False)
