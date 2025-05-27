# tests/test_api_agent.py

from fastapi.testclient import TestClient
from agents.api_agent.main import app

client = TestClient(app)

def test_quote_endpoint():
    # Smoke-test: AAPL should return status 200 and required fields
    response = client.post("/quote", json={"symbol": "AAPL"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert isinstance(data["price"], (int, float))
    assert isinstance(data["timestamp"], str)
