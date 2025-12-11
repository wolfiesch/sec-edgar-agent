from fastapi.testclient import TestClient
from src.api.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_parse_table_mocked():
    """Test table parsing with mocked parser."""
    mock_result = MagicMock()
    mock_result.markdown = "| Region | Sales |\n|---|---|"
    mock_result.structured = [{"Region": "Americas", "Sales": 100}]
    mock_result.citation = "[AAPL 10-K 2024]"
    mock_result.confidence = "high"
    mock_result.source_method = "inline-xbrl"

    with patch("src.api.routes.tables.parser.parse_from_filing", return_value=mock_result):
        response = client.post(
            "/api/v1/tables/parse",
            json={
                "ticker": "AAPL",
                "form_type": "10-K",
                "year": 2024,
                "table_name": "segment_information"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["citation"] == "[AAPL 10-K 2024]"
        assert data["markdown"] == "| Region | Sales |\n|---|---|"
