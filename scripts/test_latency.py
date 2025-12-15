
import sys
import time
import os
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agents.orchestrator import classify_query_complexity

def main():
    console = Console()
    
    test_queries = [
        # Simple queries (Should be FAST)
        ("What is Apple's revenue in 2024?", "simple", "AAPL", "get_income_statement"),
        ("Get net income for Microsoft", "simple", "MSFT", "get_income_statement"),
        ("Tesla EPS 2023", "simple", "TSLA", "get_income_statement"),
        ("What is the operating income for NVDA?", "simple", "NVDA", "get_income_statement"),
        ("Show me Google's total assets", "simple", "GOOGL", "get_balance_sheet"),
        ("Amazon debt", "simple", "AMZN", "get_balance_sheet"),
        ("Netflix cash flow", "simple", "NFLX", "get_cash_flow"),
        ("Ticker for Meta", "simple", "META", "get_company_info"),
        ("Tell me about Microsoft", "simple", "MSFT", "get_company_info"),
        
        # Medium queries (Should be MEDIUM - Ticker found but no specific tool pattern)
        ("Is MSFT profitable?", "medium", "MSFT", None), 
        
        # Complex queries (Should be COMPLEX - Needs full planner)
        ("Give me a summary of Uber", "complex", None, None), 
        ("Compare Apple and Microsoft revenue", "complex", None, None),
        ("What are the risk factors for Tesla?", "complex", None, None),
        ("How did NVDA's margins change over time?", "complex", None, None),
        ("Analyze the trend in Amazon's shipping costs", "complex", None, None),
    ]

    table = Table(title="Latency Benchmark: Query Classification")
    table.add_column("Query", style="cyan")
    table.add_column("Expected", style="green")
    table.add_column("Actual", style="yellow")
    table.add_column("Ticker", style="magenta")
    table.add_column("Tool", style="blue")
    table.add_column("Time (ms)", style="red")
    table.add_column("Status", style="bold")

    total_time = 0
    passed = 0

    for query, expected_complexity, expected_ticker, expected_tool in test_queries:
        start = time.perf_counter()
        complexity, ticker, tool, year = classify_query_complexity(query)
        duration = (time.perf_counter() - start) * 1000  # ms
        
        total_time += duration
        
        # Verification
        complexity_match = complexity == expected_complexity
        ticker_match = (expected_ticker is None) or (ticker == expected_ticker)
        tool_match = (expected_tool is None) or (tool == expected_tool)
        
        is_success = complexity_match and ticker_match and tool_match
        if is_success:
            passed += 1
            status = "[green]PASS[/green]"
        else:
            status = "[red]FAIL[/red]"
            
        table.add_row(
            query, 
            expected_complexity, 
            complexity, 
            str(ticker), 
            str(tool), 
            f"{duration:.2f}", 
            status
        )

    console.print(table)
    
    avg_latency = total_time / len(test_queries)
    console.print(f"\n[bold]Total Tests:[/bold] {len(test_queries)}")
    console.print(f"[bold]Passed:[/bold] {passed}/{len(test_queries)}")
    console.print(f"[bold]Average Classification Latency:[/bold] {avg_latency:.2f} ms")

if __name__ == "__main__":
    main()
