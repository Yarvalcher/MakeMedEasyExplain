import pytest
from MMEE_Agent.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_flask_endpoint_returns_200(client):
    """Verifies that the core dashboard HTML renders successfully with a 200 OK status."""
    res = client.get('/')
    assert res.status_code == 200
    assert b"MakeMedEasyExplain" in res.data
    assert b"query-input" in res.data
    assert b"translate-btn" in res.data
