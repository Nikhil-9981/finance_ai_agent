# tests/test_scraper_agent.py

from fastapi.testclient import TestClient
from agents.scraper_agent.main import app

client = TestClient(app)

def test_filing_endpoint():
    # Use Apple CIK (0000320193) and 10-K as test case
    payload = {"cik": "0000320193", "filing_type": "10-K"}
    response = client.post("/filing", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["cik"] == "0000320193"
    assert data["filing_type"] == "10-K"
    # document_text should be non-empty and contain the EDGAR header
    assert isinstance(data["document_text"], str)
    assert "EDGAR Filing Documents" in data["document_text"]
