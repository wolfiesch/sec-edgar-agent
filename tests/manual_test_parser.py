from src.parsers.table_parser import TableParser
import sys

def test_parser(ticker="AAPL", table="balance_sheet"):
    print(f"Testing {table} for {ticker}...")
    parser = TableParser()
    try:
        result = parser.parse_from_filing(ticker, "10-K", table, year=2024)
        print("\n--- Parsed Table ---")
        print(result.markdown)
        print("\n--- Citation ---")
        print(result.citation)
        print("\n--- Structured Data Sample ---")
        print(result.structured[:2])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    table = sys.argv[2] if len(sys.argv) > 2 else "balance_sheet"
    test_parser(ticker, table)
