import pytest
from unittest.mock import patch

@pytest.mark.integration
def test_end_to_end_flow(client):
    fake_raw = [{"raw_inst": "Uni", "raw_date": "1 Jan 2025"}]
    # Patch web.app symbols because routes resolve module-level imports there.
    with patch('web.app.GradCafeScraper') as MockScraper, \
         patch('web.app.DataCleaner') as MockCleaner, \
         patch('web.app.load_data_module.load_data') as MockLoader:
        
        MockScraper.return_value.scrape_data.return_value = fake_raw
        
        # Integration tests send Accept header for JSON
        response = client.post('/pull-data', headers={"Accept": "application/json"})
        
        assert response.status_code == 200
        assert response.json == {"ok": True}
        MockScraper.return_value.scrape_data.assert_called()
