import shutil

from sqlmodel import Session, select, func, col, SQLModel, create_engine # type: ignore
from src.config import settings
from src.data.db import engine, init_db
from src.data.db_models import JobStatus, ProcessingJob
from src.data.ingestion import ingest_filing
from src.data.vector_store import get_vector_store


async def verify_retrieval() -> None:
    print(f"🧹 Cleaning up ChromaDB at {settings.chroma_persist_dir}")
    if settings.chroma_persist_dir.exists():
        shutil.rmtree(settings.chroma_persist_dir)
        print("✅ Deleted existing chroma data.")
    else:
        print("✨ No existing data found.")

    # Force re-init of vector store global
    import src.data.vector_store
    src.data.vector_store._vector_store = None

    # Verify Search
    print("\n🔍 Verifying Search...")
    vs = get_vector_store()
    results = vs.search("What were the total sales for 2024?", ticker="AAPL", limit=3)

    if results:
        print(f"✅ Search returned {len(results)} results.")
        for i, res in enumerate(results):
            content_preview = res['content'][:200].replace('\n', ' ')
            print(f"Result {i+1}: {content_preview}...")
    else:
        print("⚠️ Search returned NO results.")


async def verify_ingestion() -> None:
    init_db()
    print("🚀 Starting Ingestion Verification")

    ticker = "AAPL"
    year = 2024
    form = "10-K"

    with Session(engine) as session:
        # Check if job exists, if not create
        stmt = select(ProcessingJob).where(
            ProcessingJob.ticker == ticker,
            ProcessingJob.year == year,
            ProcessingJob.form_type == form
        )
        session.exec(stmt).first()
        # For verification, we want to re-run if it failed or force new one?
        # But ingest_filing takes job_id.
        # Let's just create a new one every time or check PENDING.

        job = ProcessingJob(
            ticker=ticker,
            form_type=form,
            year=year,
            status=JobStatus.PENDING,
            accession_no="PENDING"
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

        print(f"📦 Created Job {job_id}. Running ingestion...")
        try:
            ingest_filing(str(job_id))
            print("✅ Ingestion complete.")
        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
            import traceback
            traceback.print_exc()
            return

    # Verify Search
    print("\n🔍 Verifying Search...")
    vs = get_vector_store()
    results = vs.search("What were the total sales for 2024?", ticker=ticker, limit=3)

    if results:
        print(f"✅ Search returned {len(results)} results.")
        for i, res in enumerate(results):
            content_preview = res['content'][:200].replace('\n', ' ')
            print(f"Result {i+1}: {content_preview}...")
    else:
        print("⚠️ Search returned NO results.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_retrieval())
