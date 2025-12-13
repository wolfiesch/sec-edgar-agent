"""
Demo script for user interviews.
Shows all Tier 0 capabilities.
"""
import sys

from sec_api_llm import SecClient


async def main() -> None:
    print("=" * 60)
    print("  SEC API for LLMs - Demo")
    print("=" * 60)
    print()

    client = SecClient(base_url="http://localhost:8000")

    try:
        # Demo 1: Table parsing with citation and section
        print("1. PARSING APPLE SEGMENT TABLE")
        print("-" * 40)
        table = client.tables.parse(
            ticker="AAPL",
            form="10-K",
            table="segment_information",
            year=2024
        )
        print(f"   Citation: {table.citation}")
        print(f"   Section:  {table.section}")
        print(f"   Rows:     {len(table.structured)}")
        print(f"   Method:   {table.metadata.get('source_method', 'inline-xbrl')}")
        print()
        print(table.markdown)
        print()

        # Demo 2: Filing metadata
        print("2. FETCHING FILING METADATA")
        print("-" * 40)
        filing = client.filings.get(ticker="AAPL", form="10-K", year=2024)
        print(f"   Ticker:       {filing.ticker}")
        print(f"   Form:         {filing.form_type}")
        print(f"   Filing date:  {filing.filing_date}")
        print(f"   Citation:     {filing.citation}")
        print(f"   URL:          {filing.url}")
        print()

        # Demo 3: Show another company (optional)
        print("3. PARSING MICROSOFT SEGMENT TABLE")
        print("-" * 40)
        msft_table = client.tables.parse(
            ticker="MSFT",
            form="10-K",
            table="segment_information",
            year=2024
        )
        print(f"   Citation: {msft_table.citation}")
        print(f"   Section:  {msft_table.section}")
        print(f"   Rows:     {len(msft_table.structured)}")
        print()
        print(msft_table.markdown)
        print()

        print("=" * 60)
        print("  ALL DEMOS COMPLETE!")
        print("=" * 60)
        print()
        print("Key Features Demonstrated:")
        print("  - Structured table extraction (not raw HTML)")
        print("  - Logical row ordering (revenue -> expenses -> profit)")
        print("  - Section-aware citations ([TICKER FORM YEAR, Item 8])")
        print("  - LLM-ready Markdown format")
        print("  - Works across multiple companies")
        print()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
