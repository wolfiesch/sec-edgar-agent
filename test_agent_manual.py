"""Manual test script for agent workflow.

Run with: uv run python test_agent_manual.py
"""

import logging
import sys

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

from src.agents.orchestrator import Orchestrator

def test_simple_query():
    """Test a simple company info query."""
    print("\n" + "=" * 80)
    print("TEST: Simple company info query")
    print("=" * 80 + "\n")

    orchestrator = Orchestrator()
    query = "What is Apple's ticker symbol?"

    print(f"Query: {query}\n")

    try:
        result = orchestrator.run(query)
        print(f"\nResult:\n{result}\n")
        print("✅ Test passed!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_query():
    """Test a financial data query."""
    print("\n" + "=" * 80)
    print("TEST: Financial data query")
    print("=" * 80 + "\n")

    orchestrator = Orchestrator()
    query = "Get Apple's latest income statement"

    print(f"Query: {query}\n")

    try:
        result = orchestrator.run(query)
        print(f"\nResult:\n{result}\n")
        print("✅ Test passed!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🤖 Testing SEC EDGAR Agent Workflow")
    print("=" * 80)

    # Check if we have API key
    from src.config import settings
    if not settings.anthropic_api_key or settings.anthropic_api_key == "":
        print("\n⚠️  Warning: ANTHROPIC_API_KEY not set in .env")
        print("This test will fail without a valid API key.")
        print("Please set ANTHROPIC_API_KEY in .env file.")
        sys.exit(1)

    results = []

    # Run tests
    results.append(("Simple Query", test_simple_query()))
    results.append(("Financial Query", test_financial_query()))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)
