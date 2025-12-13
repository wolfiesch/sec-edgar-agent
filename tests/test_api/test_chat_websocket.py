"""Tests for WebSocket chat endpoint."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestChatWebSocket:
    """Tests for the WebSocket chat endpoint."""

    def test_websocket_missing_api_key(self, client: TestClient):
        """Test that connection is rejected without API key."""
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/chat/ws"):
                pass
        # Connection should be rejected immediately (no messages sent)

    def test_websocket_invalid_api_key(self, client: TestClient):
        """Test that connection is rejected with invalid API key."""
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/chat/ws?api_key=wrong-key"):
                pass
        # Connection should be rejected immediately

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_websocket_valid_connection(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test successful WebSocket connection and query."""
        # Mock the streaming orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_streaming.return_value = iter([
            ("planning", "Analyzing your query...", None),
            ("executing", "Executing tasks...", None),
            ("complete", "Apple's revenue was $394.3 billion.", {"elapsed": 2.5}),
        ])
        mock_orchestrator_class.return_value = mock_orchestrator

        with client.websocket_connect("/api/v1/chat/ws?api_key=sec-api-demo") as websocket:
            # Send a query
            websocket.send_json({"query": "What was Apple's revenue?"})

            # Receive streaming responses
            messages = []
            for _ in range(3):  # Expect 3 messages
                data = websocket.receive_json()
                messages.append(data)

            # Verify we got all phases
            phases = [m["phase"] for m in messages]
            assert "planning" in phases
            assert "complete" in phases

            # Verify final message has the answer
            complete_msg = next(m for m in messages if m["phase"] == "complete")
            assert "revenue" in complete_msg["message"].lower()

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_websocket_invalid_json(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test that invalid JSON returns error message."""
        with client.websocket_connect("/api/v1/chat/ws?api_key=sec-api-demo") as websocket:
            # Send invalid JSON
            websocket.send_text("not valid json")

            # Should receive error message
            data = websocket.receive_json()
            assert data["phase"] == "error"
            assert "Invalid JSON" in data["message"]

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_websocket_missing_query(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test that missing query field returns error message."""
        with client.websocket_connect("/api/v1/chat/ws?api_key=sec-api-demo") as websocket:
            # Send JSON without query
            websocket.send_json({"other": "field"})

            # Should receive error message
            data = websocket.receive_json()
            assert data["phase"] == "error"
            assert "Missing" in data["message"]

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_websocket_multiple_queries(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test that multiple queries can be sent on same connection."""
        call_count = 0

        def streaming_side_effect(query):
            nonlocal call_count
            call_count += 1
            return iter([
                ("complete", f"Answer {call_count}", {"elapsed": 1.0}),
            ])

        mock_orchestrator = MagicMock()
        mock_orchestrator.run_streaming.side_effect = streaming_side_effect
        mock_orchestrator_class.return_value = mock_orchestrator

        with client.websocket_connect("/api/v1/chat/ws?api_key=sec-api-demo") as websocket:
            # Send first query
            websocket.send_json({"query": "First question"})
            data1 = websocket.receive_json()
            assert "Answer 1" in data1["message"]

            # Send second query on same connection
            websocket.send_json({"query": "Second question"})
            data2 = websocket.receive_json()
            assert "Answer 2" in data2["message"]

    @patch("src.api.routes.chat.StreamingOrchestrator")
    def test_websocket_error_handling(
        self, mock_orchestrator_class: MagicMock, client: TestClient
    ):
        """Test that orchestrator errors are handled gracefully."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.run_streaming.side_effect = RuntimeError("API error")
        mock_orchestrator_class.return_value = mock_orchestrator

        with client.websocket_connect("/api/v1/chat/ws?api_key=sec-api-demo") as websocket:
            # Send a query
            websocket.send_json({"query": "What was revenue?"})

            # Should receive error message
            data = websocket.receive_json()
            assert data["phase"] == "error"
            assert "Error processing query" in data["message"]
