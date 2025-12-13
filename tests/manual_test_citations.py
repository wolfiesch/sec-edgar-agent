from dataclasses import dataclass
from datetime import date

from src.utils.citations import Citation, create_citation_from_filing


# Mock edgar.Filing for testing
@dataclass
class MockFiling:
    form: str
    filing_date: date
    accession_no: str
    url: str
    ticker: str = None  # Some filings objects might miss this locally if not fully hydrated

def test_citation_class():
    print("\n--- Testing Citation Class ---")
    cit = Citation(
        ticker="AAPL",
        form_type="10-K",
        filing_date="2024-09-28",
        section="Item 8",
        page=45
    )
    print(f"String: {cit.to_string()}")
    print(f"Dict: {cit.to_dict()}")

    expected_str = "[AAPL 10-K 2024, Item 8, Page 45]"
    if cit.to_string() == expected_str:
        print("PASS: String format matches")
    else:
        print(f"FAIL: Expected {expected_str}, got {cit.to_string()}")

def test_create_from_filing():
    print("\n--- Testing create_citation_from_filing ---")
    mock_filing = MockFiling(
        form="10-Q",
        filing_date=date(2023, 6, 30),
        accession_no="000123-23-000123",
        url="http://sec.gov/fake",
        ticker="MSFT"
    )

    cit = create_citation_from_filing(mock_filing, section="Item 2")
    print(f"Generated: {cit.to_string()}")

    if "MSFT 10-Q 2023" in cit.to_string() and "Item 2" in cit.to_string():
        print("PASS: Factory creation successful")
    else:
         print("FAIL: Factory creation failed")

    # Test without ticker in object but passed in arg
    mock_filing_no_ticker = MockFiling(
        form="8-K",
        filing_date=date(2024, 1, 15),
        accession_no="000111-24-000001",
        url="http://sec.gov/fake"
    )
    cit2 = create_citation_from_filing(mock_filing_no_ticker, ticker="NVDA")
    print(f"Generated (Explicit Ticker): {cit2.to_string()}")
    if "NVDA 8-K 2024" in cit2.to_string():
        print("PASS: Explicit ticker handling successful")
    else:
        print("FAIL: Explicit ticker handling failed")

if __name__ == "__main__":
    test_citation_class()
    test_create_from_filing()
