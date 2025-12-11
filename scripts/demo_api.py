"""
Demo script for user interviews.
Shows all Tier 0 capabilities.
"""
from sec_api_llm import SecClient
import sys

def main():
    print("🚀 SEC API for LLMs - Demo\n")

    client = SecClient(base_url="http://localhost:8000")

    try:
        # Demo 1: Table parsing
        print("1️⃣ Parsing Apple segment table...")
        table = client.tables.parse(
            ticker="AAPL",
            form="10-K",
            table="segment_information",
            year=2024
        )
        print(f"   Citation: {table.citation}")
        print(f"   Rows: {len(table.structured)}")
        print(f"\n{table.markdown}\n")

        # Demo 2: Filing metadata
        print("2️⃣ Fetching filing metadata...")
        filing = client.filings.get(ticker="AAPL", form="10-K", year=2024)
        print(f"   Filing date: {filing.filing_date}")
        print(f"   URL: {filing.url}")
        print(f"   Citation: {filing.citation}\n")

        print("✅ All demos complete!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
