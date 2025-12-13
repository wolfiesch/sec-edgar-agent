"""Tests for SSE chat streaming endpoint."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestChatStream:
    """Tests for the SSE chat streaming endpoint."""

    def test_stream_missing_api_key(self, client: TestClient):
        """Test that request is rejected without API key."""
        response = client.get("/api/v1/chat/stream?query=test")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_stream_invalid_api_key(self, client: TestClient):
        """Test that request is rejected with invalid API key."""
        response = client.get(
            "/api/v1/chat/stream?query=test",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    def test_stream_missing_query(self, client: TestClient):
        """Test that request requires query parameter."""
        response = client.get(
            "/api/v1/chat/stream",
            headers={"X-API-Key": "sec-api-demo"},
        )
        assert response.status_code == 422  # Validation error

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_stream_success(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test successful streaming response."""
        # Mock the streaming orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_streaming.return_value = iter([
            ("planning", "Analyzing your query...", None),
            ("executing", "Executing tasks...", None),
            ("complete", "Apple's revenue was $394.3 billion.", {"elapsed": 2.5}),
        ])
        mock_orchestrator_class.return_value = mock_orchestrator

        response = client.get(
            "/api/v1/chat/stream?query=What+was+Apple's+revenue",
            headers={"X-API-Key": "sec-api-demo"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events
        events = []
        for line in response.text.split("\n"):
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                events.append(event_data)

        # Verify we got all phases
        phases = [e["phase"] for e in events]
        assert "planning" in phases
        assert "executing" in phases
        assert "complete" in phases

        # Verify final message has the answer
        complete_event = next(e for e in events if e["phase"] == "complete")
        assert "revenue" in complete_event["message"].lower()

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_stream_error_handling(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test that orchestrator errors are handled gracefully."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_streaming.side_effect = RuntimeError("API error")
        mock_orchestrator_class.return_value = mock_orchestrator

        response = client.get(
            "/api/v1/chat/stream?query=What+was+revenue",
            headers={"X-API-Key": "sec-api-demo"},
        )

        assert response.status_code == 200  # SSE streams always return 200

        # Parse SSE events
        events = []
        for line in response.text.split("\n"):
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                events.append(event_data)

        # Should have error event
        assert len(events) == 1
        assert events[0]["phase"] == "error"
        assert "Error processing query" in events[0]["message"]

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_stream_cache_headers(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test that proper cache headers are set for SSE."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_streaming.return_value = iter([
            ("complete", "Done", None),
        ])
        mock_orchestrator_class.return_value = mock_orchestrator

        response = client.get(
            "/api/v1/chat/stream?query=test",
            headers={"X-API-Key": "sec-api-demo"},
        )

        assert response.headers["cache-control"] == "no-cache"

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_stream_with_special_characters(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test that queries with special characters work."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_streaming.return_value = iter([
            ("complete", "Answer with $symbols & more", None),
        ])
        mock_orchestrator_class.return_value = mock_orchestrator

        # Query with special characters
        response = client.get(
            "/api/v1/chat/stream",
            params={"query": "What's Apple's Q1 2023 revenue?"},
            headers={"X-API-Key": "sec-api-demo"},
        )

        assert response.status_code == 200

        # Parse and verify
        events = []
        for line in response.text.split("\n"):
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                events.append(event_data)

        assert len(events) == 1
        assert events[0]["phase"] == "complete"
