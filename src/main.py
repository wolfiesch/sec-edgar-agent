"""SEC EDGAR Financial Agent - CLI Entry Point."""

import json
import logging
import sys
from typing import Any

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

# Create Typer app
app = typer.Typer(
    name="edgar-agent",
    help="SEC EDGAR Financial Agent - AI-powered financial research",
    add_completion=False,
)


def print_welcome() -> None:
    """Print welcome message."""
    console.print(
        Panel(
            "[bold blue]SEC EDGAR Financial Agent[/bold blue]\n\n"
            "AI-powered financial research using SEC filings.\n"
            "Type [bold green]/help[/bold green] for commands or ask a question.\n"
            "Type [bold red]/quit[/bold red] to exit.",
            title="Welcome",
            border_style="blue",
        )
    )


def print_help() -> None:
    """Print help information."""
    table = Table(title="Available Commands", show_header=True)
    table.add_column("Command", style="green")
    table.add_column("Description")

    table.add_row("/help", "Show this help message")
    table.add_row("/tools", "List available tools")
    table.add_row("/company TICKER", "Get company info")
    table.add_row("/filings TICKER", "List recent filings")
    table.add_row("/financials TICKER", "Get financial summary")
    table.add_row("/insider TICKER", "Get insider trading activity")
    table.add_row("/clear", "Clear the screen")
    table.add_row("/quit", "Exit the agent")

    console.print(table)
    console.print("\n[dim]Or just type a natural language question![/dim]")


def handle_command(command: str) -> bool:
    """
    Handle slash commands.

    Returns True if command was handled, False to exit.
    """
    # Import tools module to register all tools
    from src.tools import registry

    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "/quit" or cmd == "/exit":
        console.print("[yellow]Goodbye![/yellow]")
        return False

    elif cmd == "/help":
        print_help()

    elif cmd == "/clear":
        console.clear()
        print_welcome()

    elif cmd == "/tools":
        tools = registry.list_tools()
        console.print(Panel(
            "\n".join(f"• {tool}" for tool in tools),
            title="Available Tools",
        ))

    elif cmd == "/company":
        if not args:
            console.print("[red]Usage: /company TICKER[/red]")
        else:
            with console.status(f"[cyan]Looking up {args.upper()}...[/cyan]"):
                result = registry.execute("get_company_info", {"ticker": args})
            if result.success:
                data = result.result
                table = Table(title=f"{data['name']} ({data['ticker']})")
                table.add_column("Field", style="cyan")
                table.add_column("Value")
                table.add_row("CIK", data.get("cik", "N/A"))
                table.add_row("Industry", data.get("sic_description", "N/A"))
                table.add_row("Exchange", data.get("exchange", "N/A"))
                console.print(table)
            else:
                console.print(f"[red]Error: {result.error}[/red]")

    elif cmd == "/filings":
        if not args:
            console.print("[red]Usage: /filings TICKER[/red]")
        else:
            with console.status(f"[cyan]Fetching filings for {args.upper()}...[/cyan]"):
                result = registry.execute("search_filings", {"ticker": args, "limit": 10})
            if result.success:
                data = result.result
                table = Table(title=f"Recent Filings for {data['company']}")
                table.add_column("Date", style="cyan")
                table.add_column("Form")
                table.add_column("Accession Number")
                for f in data["filings"]:
                    table.add_row(f["filing_date"], f["form_type"], f["accession_number"])
                console.print(table)
            else:
                console.print(f"[red]Error: {result.error}[/red]")

    elif cmd == "/financials":
        if not args:
            console.print("[red]Usage: /financials TICKER[/red]")
        else:
            with console.status(f"[cyan]Fetching financials for {args.upper()}...[/cyan]"):
                result = registry.execute("get_income_statement", {"ticker": args, "periods": 3})
            if result.success and result.result.get("success"):
                data = result.result
                console.print(Panel(
                    f"[bold]{args.upper()}[/bold] - {data['periods']} periods of financial data",
                    title="Income Statement",
                ))
                for stmt in data.get("statements", []):
                    console.print(f"\n[cyan]FY{stmt['fiscal_year']}[/cyan]:")
                    console.print(json.dumps(stmt.get("data", {}), indent=2, default=str)[:1000])
            else:
                error = result.error or result.result.get("error", "Unknown error")
                console.print(f"[red]Error: {error}[/red]")

    elif cmd == "/insider":
        if not args:
            console.print("[red]Usage: /insider TICKER[/red]")
        else:
            with console.status(f"[cyan]Fetching insider trades for {args.upper()}...[/cyan]"):
                result = registry.execute("get_insider_trades", {"ticker": args})
            if result.success and result.result.get("success"):
                data = result.result
                if data.get("by_insider"):
                    table = Table(title=f"Insider Trading - {args.upper()}")
                    table.add_column("Insider", style="cyan")
                    table.add_column("Title")
                    table.add_column("Bought", style="green")
                    table.add_column("Sold", style="red")
                    for insider in data["by_insider"]:
                        table.add_row(
                            insider["name"],
                            insider.get("title", ""),
                            f"{insider['total_bought']:,.0f}",
                            f"{insider['total_sold']:,.0f}",
                        )
                    console.print(table)
                else:
                    console.print(f"[yellow]No recent insider transactions for {args.upper()}[/yellow]")
            else:
                error = result.error or result.result.get("error", "Unknown error")
                console.print(f"[red]Error: {error}[/red]")

    else:
        console.print(f"[yellow]Unknown command: {cmd}. Type /help for available commands.[/yellow]")

    return True


def run_chat_loop() -> None:
    """Run the interactive chat loop."""
    # Import here to register tools
    from src.tools import registry

    print_welcome()

    while True:
        try:
            # Get user input
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()

            if not user_input:
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                if not handle_command(user_input):
                    break
                continue

            # For now, provide helpful guidance
            # Full AI agent integration will come in Phase 2
            console.print(
                "\n[yellow]AI agent mode coming soon![/yellow]\n"
                "For now, use these commands:\n"
                "• [green]/company TICKER[/green] - Company info\n"
                "• [green]/filings TICKER[/green] - Recent filings\n"
                "• [green]/financials TICKER[/green] - Financial data\n"
                "• [green]/insider TICKER[/green] - Insider trades\n"
            )

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit to exit[/yellow]")
        except EOFError:
            break


@app.command()
def chat() -> None:
    """Start an interactive financial research session."""
    run_chat_loop()


@app.command()
def company(ticker: str) -> None:
    """Get information about a company."""
    from src.tools import registry

    with console.status(f"[cyan]Looking up {ticker.upper()}...[/cyan]"):
        result = registry.execute("get_company_info", {"ticker": ticker})

    if result.success:
        console.print_json(data=result.result)
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


@app.command()
def filings(
    ticker: str,
    form_type: str = typer.Option("10-K", "--form", "-f", help="Form type"),
    limit: int = typer.Option(5, "--limit", "-n", help="Number of filings"),
) -> None:
    """List SEC filings for a company."""
    from src.tools import registry

    with console.status(f"[cyan]Fetching {form_type} filings for {ticker.upper()}...[/cyan]"):
        result = registry.execute(
            "search_filings",
            {"ticker": ticker, "form_type": form_type, "limit": limit},
        )

    if result.success:
        console.print_json(data=result.result)
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


@app.command()
def financials(
    ticker: str,
    periods: int = typer.Option(3, "--periods", "-p", help="Number of periods"),
) -> None:
    """Get financial statements for a company."""
    from src.tools import registry

    with console.status(f"[cyan]Fetching financials for {ticker.upper()}...[/cyan]"):
        result = registry.execute(
            "get_income_statement",
            {"ticker": ticker, "periods": periods},
        )

    if result.success:
        console.print_json(data=result.result)
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """SEC EDGAR Financial Agent - AI-powered financial research."""
    if ctx.invoked_subcommand is None:
        # Default to chat mode
        run_chat_loop()


if __name__ == "__main__":
    app()
