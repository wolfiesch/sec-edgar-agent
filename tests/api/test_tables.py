from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

def test_parse_table_mocked() -> None:
    """Test table parsing with mocked parser and repository."""
    mock_result = MagicMock()
    mock_result.markdown = "| Region | Sales |\n|---|---|"
    mock_result.structured = [{"Region": "Americas", "Sales": 100}]
    mock_result.citation = "[AAPL 10-K 2024, Item 8]"
    mock_result.confidence = "high"
    mock_result.source_method = "inline-xbrl"
    mock_result.section = "Item 8"

    # Mock both the repository (to avoid DB dependency) and the parser
    with patch("src.api.routes.tables.TableRepository") as mock_repo_cls:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get.return_value = None  # No cached result
        mock_repo.create.return_value = None

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
            assert data["citation"] == "[AAPL 10-K 2024, Item 8]"
            assert data["section"] == "Item 8"
            assert data["markdown"] == "| Region | Sales |\n|---|---|"
