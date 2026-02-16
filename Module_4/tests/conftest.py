import pytest
import sys
import os
from unittest.mock import MagicMock

# 1. Force 'src' to be the root for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# 2. Global DB Mock
# We need a real Exception class for 'except psycopg.Error' to work
mock_psycopg = MagicMock()
class MockPsycopgError(Exception):
    pass
mock_psycopg.Error = MockPsycopgError
mock_psycopg.connect = MagicMock()
sys.modules['psycopg'] = mock_psycopg

# 3. App Fixtures
@pytest.fixture
def app():
    # Import from 'app', NOT 'src.app' to avoid double-loading
    from src.app import create_app
    app = create_app({'TESTING': True})
    yield app

@pytest.fixture
def client(app):
    return app.test_client()