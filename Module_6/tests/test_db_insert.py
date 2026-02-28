import pytest
from unittest.mock import MagicMock, patch
from db import load_data as load_data_module

@pytest.mark.db
def test_insert_on_pull():
    mock_json = [{"Program Name": "CS", "University": "Uni", "Comments": "", "Date of Information Added to Grad Café": "1 Jan", "Applicant Status": "Accepted"}]
    with patch("builtins.open", new_callable=MagicMock), \
         patch("json.load", return_value=mock_json), \
         patch("psycopg.connect") as mock_conn:
        
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        load_data_module.load_data("dummy.json", reset=True)
        assert mock_cursor.execute.call_count >= 1
