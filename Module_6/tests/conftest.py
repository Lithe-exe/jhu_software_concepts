import pytest
import sys
import os
from unittest.mock import MagicMock

# 1. Force 'src' to be the root for imports
# This allows 'import app' to work directly, avoiding 'src.app' duplication
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# 2. Global DB Mock
mock_psycopg = MagicMock()
class MockPsycopgError(Exception):
    pass
mock_psycopg.Error = MockPsycopgError
mock_psycopg.connect = MagicMock()
sys.modules['psycopg'] = mock_psycopg

# 3. App Fixtures
@pytest.fixture
def app():
    # Reset globals to ensure clean state for every test
    import web.app as app_module
    app_module.IS_BUSY = False
    app_module.CACHED_ANALYSIS = None
    
    from web.app import create_app
    app_instance = create_app({'TESTING': True})
    yield app_instance

@pytest.fixture
def client(app):
    return app.test_client()
