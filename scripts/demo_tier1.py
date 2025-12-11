from sec_api_llm import SecClient
import time
import os

# Set dummy key if not in env for demo structure
if not os.getenv("SEC_API_KEY"):
    os.environ["SEC_API_KEY"] = "sec-api-demo"

def demo_tier1():
    print("--- Tier 1 Feature Demo ---")
    client = SecClient(base_url="http://localhost:8000/api/v1")

    # 1. Trigger Ingestion
    print("\n[Step 1] Triggering Ingestion for AAPL 2024 10-K...")
    try:
        # Note: year 2025 in recent apple filing meta
        ingest_resp = client.ingest.trigger(ticker="AAPL", form_type="10-K", year=2025)
        job_id = ingest_resp["job_id"]
        print(f"Ingestion started. Job ID: {job_id}")
    except Exception as e:
        print(f"Ingestion failed (maybe server not running?): {e}")
        return

    # 2. Poll Status
    print("\n[Step 2] Polling Status...")
    status = "PENDING"
    while status in ["PENDING", "PROCESSING"]:
        job_status = client.ingest.get(job_id)
        status = job_status["status"]
        print(f"Status: {status}")
        if status in ["DONE", "FAILED"]:
            break
        time.sleep(2)

    if status == "FAILED":
        print("Ingestion failed. Stopping demo.")
        return

    # 3. Search
    query = "What were the net sales for 2025?"
    print(f"\n[Step 3] Semantic Search: '{query}'")
    search_resp = client.search.query(query=query, ticker="AAPL")
    for res in search_resp.results:
        print(f"- Score {res.score:.2f}: {res.content[:100]}...")

    # 4. Chat
    print(f"\n[Step 4] Chat RAG: '{query}'")
    chat_resp = client.chat.create(
        messages=[{"role": "user", "content": query}],
        ticker="AAPL"
    )
    print("Answer:")
    print(chat_resp.answer)
    print("Citations:", chat_resp.citations)

if __name__ == "__main__":
    demo_tier1()
