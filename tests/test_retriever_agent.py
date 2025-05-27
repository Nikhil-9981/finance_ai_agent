# tests/test_retriever_agent.py

import os
import pickle
import faiss

from fastapi.testclient import TestClient
from agents.retriever_agent.main import app

# Fixture: Ensure index + meta exist
def test_index_files_exist():
    assert os.path.exists("data_ingestion/faiss_index"), "FAISS index missing"
    assert os.path.exists("data_ingestion/faiss_index.meta"), "Metadata missing"

client = TestClient(app)

def test_retrieve_endpoint():
    # Simple sanity check; returns 5 results without error
    response = client.post("/retrieve", json={"query": "Asia tech stocks", "top_k": 3})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["query"] == "Asia tech stocks"
    assert isinstance(data["results"], list)
    assert len(data["results"]) <= 3
    for chunk in data["results"]:
        assert "text" in chunk
        assert "source" in chunk
        assert isinstance(chunk["score"], float)
