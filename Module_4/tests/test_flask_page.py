import pytest
from src.app import app as flask_app 

@pytest.mark.web
def test_app_factory_config(client):
    """Test app factory and required routes."""
    assert client.application.config['TESTING'] is True
    
    # Check routes exist in the map
    rules = [str(p) for p in client.application.url_map.iter_rules()]
    assert '/' in rules
    assert '/pull-data' in rules
    assert '/update-analysis' in rules

@pytest.mark.web
def test_analysis_page_load(client):
    """Test GET /analysis (index) loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    assert "Analysis" in html
    # Check for buttons via text or data-testid (using text here as fallback)
    assert "Pull Data" in html
    assert "Update Analysis" in html
    assert "Answer:" in html