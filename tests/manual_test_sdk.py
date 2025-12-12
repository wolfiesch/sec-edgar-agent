from sec_api_llm import SecClient
import sys
import time

def test_sdk_tables():
    print("Testing SDK Table Parsing...")
    # Point to localhost where API should be running
    client = SecClient(base_url="http://localhost:8000")
    
    try:
        # 1. Test Balance Sheet
        print("\nRequesting AAPL Balance Sheet...")
        bs = client.tables.parse("AAPL", "10-K", "balance_sheet", year=2024)
        print("Success!")
        print(f"Citation: {bs.citation}")
        print(f"Confidence: {bs.confidence}")
        print(f"Markdown length: {len(bs.markdown)}")
        
        # 2. Test Income Statement
        print("\nRequesting AAPL Income Statement...")
        inc = client.tables.parse("AAPL", "10-K", "income_statement", year=2024)
        print("Success!")
        print(f"Citation: {inc.citation}")
        
    except Exception as e:
        print(f"\nFAILED: {e}")
        # Print detailed info if it's an API error
        if hasattr(e, 'response'):
             print(e.response.text)

def test_sdk_filings():
    print("\nTesting SDK Filings...")
    client = SecClient(base_url="http://localhost:8000")
    try:
        f = client.filings.get("AAPL", "10-K", year=2024)
        print(f"Success! Found filing {f.accession_no}")
        print(f"URL: {f.url}")
        print(f"Sections: {f.sections_available}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    # Wait for server to be ready (user must run server separately)
    test_sdk_tables()
    test_sdk_filings()
