import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.buttons
def test_pull_data_endpoint(client):
    """Test POST /pull-data triggers scraper/loader and returns 200."""
    with patch('src.app.GradCafeScraper') as mock_scrape_cls, \
         patch('src.app.DataCleaner') as mock_clean_cls, \
         patch('src.app.board.load_data.load_data') as mock_load:
        
        # Setup mocks to avoid errors
        mock_scraper = mock_scrape_cls.return_value
        mock_scraper.scrape_data.return_value = []
        
        # Send request accepting JSON to get the JSON response
        response = client.post('/pull-data', headers={"Accept": "application/json"})
        
        assert response.status_code == 200
        assert response.json == {"ok": True}
        
        # Verify ETL chain was called
        mock_scraper.scrape_data.assert_called()
        mock_clean_cls.assert_called()
        mock_load.assert_called()

@pytest.mark.buttons
def test_update_analysis_endpoint(client):
    """Test POST /update-analysis returns redirect (302) or 200 depending on implementation."""
    response = client.post('/update-analysis')
    # Default Flask redirect is 302
    assert response.status_code == 302 

@pytest.mark.buttons
def test_busy_gating(client):
    """Test that endpoints return 409 when busy."""
    # Manually set the busy flag
    import src.app
    src.app.IS_BUSY = True
    
    try:
        response_update = client.post('/update-analysis')
        assert response_update.status_code == 409
        assert response_update.json['busy'] is True
        
        response_pull = client.post('/pull-data')
        assert response_pull.status_code == 409
        assert response_pull.json['busy'] is True
    finally:
        # Reset for other tests
        src.app.IS_BUSY = False