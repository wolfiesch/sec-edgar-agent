
from bs4 import BeautifulSoup
from edgar import Company  # type: ignore

from src.parsers.table_parser import TableParser


def debug_filing(ticker="AAPL", form="10-K", year=2024):
    print(f"DEBUG: Fetching {ticker} {form} {year}")

    company = Company(ticker)
    filings = company.get_filings(form=form)

    selected_filing = None
    for f in filings:
        if f.filing_date.year == year:
            selected_filing = f
            break

    if not selected_filing:
        print("Filing not found")
        return

    html = selected_filing.html()
    soup = BeautifulSoup(html, "lxml")

    # 1. Inspect Contexts
    parser = TableParser()
    contexts = parser._parse_contexts(soup)
    print(f"\nFound {len(contexts)} contexts")

    durations = [c for c in contexts.values() if c.type == "duration"]
    print(f"Duration contexts: {len(durations)}")

    # Print a few duration contexts to see dates
    for c in durations[:5]:
        print(f"  {c.id}: {c.period} (Dims: {c.dims})")

    # 2. Inspect Tags
    tags = soup.find_all("ix:nonfraction")
    print(f"\nFound {len(tags)} ix:nonfraction tags")

    # Check for specific target metrics
    targets = ["Revenue", "Revenues", "NetIncome", "NetCashProvidedByUsedInOperatingActivities"]

    found_targets = {}
    for t in tags:
        name = t.get("name", "")
        val = t.get_text(strip=True)
        ctx = t.get("contextref")

        for target in targets:
            if target in name:
                if target not in found_targets:
                    found_targets[target] = []
                if len(found_targets[target]) < 5:
                    found_targets[target].append(f"{name} = {val} (ctx={ctx})")

    print("\n--- Target Sample Matches ---")
    for k, v in found_targets.items():
        print(f"{k}:")
        for item in v:
            print(f"  {item}")

if __name__ == "__main__":
    debug_filing()
