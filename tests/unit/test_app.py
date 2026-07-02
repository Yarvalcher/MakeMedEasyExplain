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

from unittest.mock import patch, AsyncMock

@patch('MMEE_Agent.app.run_agent_pipeline', new_callable=AsyncMock)
def test_rate_limiting_returns_429(mock_pipeline, client):
    """Verifies that IP-based rate limiting returns 429 Too Many Requests after exceeding 5 requests."""
    mock_pipeline.return_value = "This is a valid test analogy explanation."
    
    # Send 5 requests (should be 200 OK)
    for _ in range(5):
        res = client.post('/translate', json={"query": "heart attack"})
        assert res.status_code == 200
        
    # The 6th request should exceed the limit and return 429
    res = client.post('/translate', json={"query": "heart attack"})
    assert res.status_code == 429
    assert b"Rate limit exceeded" in res.data
