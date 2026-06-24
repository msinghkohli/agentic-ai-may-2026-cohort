from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest
import os

# Set environment variables for testing
os.environ["ATLASSIAN_EMAIL"] = "test@example.com"
os.environ["ATLASSIAN_API_KEY"] = "test_key"
os.environ["MODEL_ID"] = "mock_model"

mock_manager = MagicMock()
mock_crew = MagicMock()
mock_crew.manager_agent = mock_manager

with patch("src.config.setup_tracing"):
    with patch("src.tools.PIO"):
        with patch("src.jira_management.crew_v2.create_crew", return_value=mock_crew):
            from src.jira_server.server import app

client = TestClient(app)

def test_agent_card_unauthenticated():
    """Verify that the GET / endpoint returns the public Agent Card without authentication."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jira Management Agent"
    assert "skills" in data
    assert "security_schemes" in data

def test_rpc_endpoint_unauthenticated():
    """Verify that POST / rpc requests without Authorization headers are rejected with 401."""
    response = client.post("/", json={
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": "1",
        "params": {}
    })
    assert response.status_code == 401
    assert "Unauthorized" in response.json()["error"]

def test_rpc_endpoint_invalid_token():
    """Verify that POST / rpc requests with an invalid Bearer token are rejected with 401."""
    headers = {"Authorization": "Bearer InvalidToken"}
    response = client.post("/", json={
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": "1",
        "params": {}
    }, headers=headers)
    assert response.status_code == 401
    assert "Unauthorized" in response.json()["error"]

@patch("src.jira_server.server.create_crew")
def test_rpc_message_send_success(mock_create_crew):
    """Verify that a valid JSON-RPC message/send request to the server runs the crew and returns the task result."""
    # Mock the crew execution
    mock_crew = MagicMock()
    mock_result = MagicMock()
    mock_result.raw = "Ticket TIME-123 is In Progress."
    mock_crew.kickoff.return_value = mock_result
    mock_create_crew.return_value = mock_crew

    headers = {"Authorization": "Bearer OrangeJiraToken"}
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": "request-id-123",
        "params": {
            "id": "task-uuid-456",
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": "What is the status of ticket TIME-123?"
                    }
                ]
            }
        }
    }

    response = client.post("/", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "request-id-123"
    
    result = data["result"]
    assert result["id"] == "task-uuid-456"
    assert result["status"]["state"] == "completed"
    assert len(result["artifacts"]) == 1
    
    artifact = result["artifacts"][0]
    assert artifact["name"] == "jira_status_report"
    assert artifact["parts"][0]["text"] == "Ticket TIME-123 is In Progress."
