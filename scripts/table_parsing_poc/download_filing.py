"""Download Apple 10-K filing for table parsing investigation.

This script downloads the latest Apple 10-K filing and extracts:
1. Full HTML document
2. Item 8 (Financial Statements) section
3. Segment Information table

Usage:
    python scripts/table_parsing_poc/download_filing.py
"""

from pathlib import Path

import edgar
from edgar import Company  # type: ignore
from rich.console import Console
from rich.progress import Progress

console = Console()

# Set SEC identity (required by SEC)
edgar.set_identity("Wolfgang Schoenberger wolfgang@example.com")

# Paths
DATA_DIR = Path("data/test_tables")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_apple_10k() -> dict:
    """Download latest Apple 10-K filing.

    Returns:
        dict with filing metadata and content
    """
    console.print("\n[bold blue]📥 Downloading Apple 10-K Filing[/bold blue]\n")

    with Progress() as progress:
        task = progress.add_task("[cyan]Fetching Apple filings...", total=100)

        # Get Apple company
        apple = Company("AAPL")
        progress.update(task, advance=30)

        # Get latest 10-K
        console.print(f"[green]✓[/green] Found company: {apple.name}")
        filings = apple.get_filings(form="10-K")
        progress.update(task, advance=30)

        if not filings:
            raise ValueError("No 10-K filings found for Apple")

        latest_10k = filings[0]
        console.print(
            f"[green]✓[/green] Latest 10-K: {latest_10k.filing_date} (Fiscal {latest_10k.filing_date.year})"
        )
        progress.update(task, advance=40)

    # Get filing details
    filing_info = {
        "ticker": "AAPL",
        "company_name": apple.name,
        "form": "10-K",
        "filing_date": str(latest_10k.filing_date),
        "fiscal_year": latest_10k.filing_date.year,
        "accession_number": latest_10k.accession_no,
    }

    console.print("\n[bold green]Filing Information:[/bold green]")
    for key, value in filing_info.items():
        console.print(f"  {key}: {value}")

    return latest_10k, filing_info


def extract_html_content(filing) -> str:
    """Extract full HTML content from filing.

    Args:
        filing: EdgarTools Filing object

    Returns:
        str: Full HTML content
    """
    console.print("\n[bold blue]📄 Extracting HTML Content[/bold blue]\n")

    # Get the primary document (10-K HTML)
    html_content = filing.html()

    console.print(f"[green]✓[/green] Extracted HTML ({len(html_content):,} characters)")

    # Save to file
    output_path = DATA_DIR / "aapl_10k_full.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    console.print(f"[green]✓[/green] Saved to: {output_path}")

    return html_content


def identify_segment_table(html_content: str) -> None:
    """Identify and extract Segment Information table.

    This function uses BeautifulSoup to parse the HTML and locate the
    segment information table based on header content.

    Args:
        html_content: Full HTML content of 10-K
    """
    from bs4 import BeautifulSoup

    console.print("\n[bold blue]🔍 Identifying Segment Information Table[/bold blue]\n")

    soup = BeautifulSoup(html_content, "lxml")

    # Find all tables
    tables = soup.find_all("table")
    console.print(f"[cyan]Found {len(tables)} tables in document[/cyan]")

    # Search for segment table (look for "Americas", "Europe", "Greater China")
    segment_keywords = ["Americas", "Europe", "Greater China", "Japan", "Asia Pacific"]

    for idx, table in enumerate(tables):
        table_text = table.get_text()

        # Check if table contains segment keywords
        matches = sum(1 for keyword in segment_keywords if keyword in table_text)

        if matches >= 3:  # At least 3 regions present
            console.print(
                f"\n[green]✓[/green] Found potential segment table (Table #{idx + 1})"
            )
            console.print(f"  Matched {matches}/{len(segment_keywords)} region keywords")

            # Save table HTML
            table_path = DATA_DIR / f"aapl_segment_table_{idx + 1}.html"
            with open(table_path, "w", encoding="utf-8") as f:
                f.write(str(table))

            console.print(f"  Saved to: {table_path}")

            # Show preview
            console.print("\n[bold]Table Preview (first 500 chars):[/bold]")
            preview = table_text[:500].strip()
            console.print(f"[dim]{preview}...[/dim]\n")

    console.print(
        "\n[yellow]→[/yellow] Manually verify the correct table in data/test_tables/"
    )


def main() -> None:
    """Main execution function."""
    try:
        # Download filing
        filing, filing_info = download_apple_10k()

        # Extract HTML
        html_content = extract_html_content(filing)

        # Identify segment table
        identify_segment_table(html_content)

        # Save filing metadata
        import json

        metadata_path = DATA_DIR / "filing_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(filing_info, f, indent=2)

        console.print(
            f"\n[bold green]✅ Download Complete![/bold green]"
            f"\n\n[yellow]Next Steps:[/yellow]"
            f"\n  1. Review extracted tables in {DATA_DIR}/"
            f"\n  2. Identify the correct Segment Information table"
            f"\n  3. Create ground truth CSV from manual transcription"
            f"\n"
        )

    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        raise


if __name__ == "__main__":
    main()
