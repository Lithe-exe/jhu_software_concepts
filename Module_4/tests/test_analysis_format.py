import pytest
from unittest.mock import patch

@pytest.mark.analysis
def test_labels_and_rounding(client):
    mock_data = {'q1': 100, 'q2': "33.33"}
    with patch('board.query_data.DataAnalyzer.get_analysis', return_value=mock_data):
        response = client.get('/')
        assert "Answer:" in response.data.decode('utf-8')
        assert "33.33" in response.data.decode('utf-8')