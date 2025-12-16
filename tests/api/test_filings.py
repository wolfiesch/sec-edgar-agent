from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

def test_get_filing_404() -> None:
    """Test filing endpoint with mocks."""
    mock_filing = MagicMock()
    mock_filing.filing_date.year = 2024
    mock_filing.filing_date.__str__.return_value = "2024-01-01"
    mock_filing.accession_no = "000123"
    mock_filing.url = "http://sec.gov/filing"
    mock_filing.form = "10-K"
    mock_filing.ticker = "AAPL" # Ensure ticker is present for citation

    # Patch at the import location in the routes module
    with patch("src.api.routes.filings.Company") as mock_company_cls:
        mock_company = mock_company_cls.return_value
        mock_company.get_filings.return_value = [] # No filings found at all

        response = client.get("/api/v1/filings/AAPL/10-K?year=2024")

        assert response.status_code == 404
        data = response.json()
        # When no filings exist at all, the error message doesn't include the year
        assert data["detail"] == "No 10-K filing found for AAPL"

def test_get_filing_mocked() -> None:
    """Test filing endpoint with mocks."""
    mock_filing = MagicMock()
    mock_filing.filing_date.year = 2024
    mock_filing.filing_date.__str__.return_value = "2024-01-01"
    mock_filing.accession_no = "000123"
    mock_filing.url = "http://sec.gov/filing"
    mock_filing.form = "10-K"
    mock_filing.ticker = "AAPL" # Ensure ticker is present for citation

    # Patch at the import location in the routes module
    with patch("src.api.routes.filings.Company") as mock_company_cls:
        mock_company = mock_company_cls.return_value
        mock_company.get_filings.return_value = [mock_filing]

        response = client.get("/api/v1/filings/AAPL/10-K?year=2024")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["form_type"] == "10-K"
        assert "citation" in data


def test_download_filing_html_invalid_accession() -> None:
    """Test HTML download with invalid accession number format."""
    response = client.get("/api/v1/filings/invalid-accession/html")

    assert response.status_code == 400
    data = response.json()
    assert "Invalid accession number format" in data["detail"]


def test_list_sections_mocked() -> None:
    """Test section listing with mocked filing."""
    from datetime import date

    mock_filing = MagicMock()
    mock_filing.filing_date = date(2024, 1, 15)
    mock_filing.accession_number = "0000320193-24-000123"
    mock_filing.text.return_value = "ITEM 1 Business\nITEM 1A Risk Factors\nITEM 7 MD&A"

    with patch("src.api.routes.filings.Company") as mock_company_cls:
        mock_company = mock_company_cls.return_value
        mock_company.get_filings.return_value = [mock_filing]

        response = client.get("/api/v1/filings/AAPL/10-K/sections")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["ticker"] == "AAPL"
        assert data["form_type"] == "10-K"
        assert "sections" in data
        assert len(data["sections"]) > 0


def test_list_sections_404() -> None:
    """Test section listing when no filings exist."""
    with patch("src.api.routes.filings.Company") as mock_company_cls:
        mock_company = mock_company_cls.return_value
        mock_company.get_filings.return_value = []

        response = client.get("/api/v1/filings/AAPL/10-K/sections")

        assert response.status_code == 404
