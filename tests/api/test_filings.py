from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

def test_get_filing_mocked():
    """Test filing endpoint with mocks."""
    mock_filing = MagicMock()
    mock_filing.filing_date.year = 2024
    mock_filing.filing_date.__str__.return_value = "2024-01-01"
    mock_filing.accession_no = "000123"
    mock_filing.url = "http://sec.gov/filing"
    mock_filing.form = "10-K"
    mock_filing.ticker = "AAPL" # Ensure ticker is present for citation

    with patch("edgar.Company") as mock_company_cls:
        mock_company = mock_company_cls.return_value
        mock_company.get_filings.return_value = [mock_filing]

        response = client.get("/api/v1/filings/AAPL/10-K?year=2024")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["form_type"] == "10-K"
        assert "citation" in data
