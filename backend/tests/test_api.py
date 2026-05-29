import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from main import app

# Set a dummy admin key for testing
os.environ["ADMIN_SECRET_KEY"] = "test-admin-key"

client = TestClient(app)

@patch("api.chat.query_rag")
def test_chat_endpoint_success(mock_query_rag):
    """Test the POST /api/chat endpoint with a valid RAG response."""
    class MockRAGResult:
        answer = "Mocked answer for reject code 75."
        source_documents = []
        source_scores = []
        
    mock_query_rag.return_value = MockRAGResult()
    
    payload = {
        "message": "What is reject code 75?",
        "session_id": "test_session_123"
    }
    
    # Send request with a specific IP header to avoid rate-limiting cross-test conflicts
    response = client.post("/api/chat", json=payload, headers={"X-Forwarded-For": "127.0.0.1"})
    
    assert response.status_code == 200
    data = response.json()
    assert "Mocked answer for reject code 75." in data["answer"]
    assert data["session_id"] == "test_session_123"
    assert "response_time_ms" in data

@patch("api.chat.get_document_count")
def test_health_endpoint(mock_get_document_count):
    """Test the GET /api/health endpoint."""
    mock_get_document_count.return_value = 41
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["chroma_document_count"] == 41
    
def test_ingest_requires_auth():
    """Test that the POST /api/ingest endpoint requires the X-Admin-Key header."""
    # Attempt without header
    response = client.post("/api/ingest")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Attempt with wrong header
    response = client.post("/api/ingest", headers={"X-Admin-Key": "wrong-key"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Could not validate credentials"
