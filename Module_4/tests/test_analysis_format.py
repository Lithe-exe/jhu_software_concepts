import pytest
from unittest.mock import patch


# Verifies the rendered page shows analysis labels and preserves rounded values.
@pytest.mark.analysis
def test_labels_and_rounding(client):
    """Checks that mocked analysis data is rendered with expected text formatting."""
    mock_data = {'q1': 100, 'q2': "33.33"}
    with patch('board.query_data.DataAnalyzer.get_analysis', return_value=mock_data):
        response = client.get('/')
        assert "Answer:" in response.data.decode('utf-8')
        assert "33.33" in response.data.decode('utf-8')
