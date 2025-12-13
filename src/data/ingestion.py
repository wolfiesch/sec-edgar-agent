"""Background ingestion workflow for pulling filings into the vector store."""
import structlog
from edgar import Company  # type: ignore
from sqlmodel import Session

from src.data.db import engine
from src.data.db_models import JobStatus, ProcessingJob
from src.data.vector_store import get_vector_store

logger = structlog.get_logger()


def ingest_filing(job_id: str) -> None:
    """Background task to ingest a filing."""
    logger.info("Starting ingestion job", job_id=job_id)

    with Session(engine) as session:
        job = session.get(ProcessingJob, job_id)
        if not job:
            logger.error("Job not found", job_id=job_id)
            return

        try:
            # Update status to PROCESSING
            job.status = JobStatus.PROCESSING
            session.add(job)
            session.commit()
            session.refresh(job)

            # 1. Fetch Filing
            logger.info("Fetching filing", ticker=job.ticker, form=job.form_type)
            company = Company(job.ticker)
            filings = company.get_filings(form=job.form_type)

            # Filter by year (basic logic: matches filing date year)
            target_filing = None
            if filings:
                for f in filings:
                    # Parse date string "YYYY-MM-DD"
                    f_year = int(str(f.filing_date).split("-")[0])
                    if f_year == job.year:
                        target_filing = f
                        break

            if not target_filing:
                raise ValueError(f"No {job.form_type} found for {job.ticker} in {job.year}")

            logger.info("Filing found", accession=target_filing.accession_no)

            # 2. Get Content (Markdown)
            # This handles tables as Markdown tables (preservation strategy)
            content = target_filing.markdown()
            if not content:
                raise ValueError("Empty markdown content")

            # 3. Clean Vector Store (Idempotency)
            vector_store = get_vector_store()
            deleted = vector_store.delete_filing(job.ticker, target_filing.accession_no)
            if deleted:
                logger.info("Cleared existing vectors", count=deleted)

            # 4. Chunk & Store
            # section_name="Full Report" is a simplification.
            # ideally we iterate sections.
            # But edgar.markdown() is one blob.
            # We rely on MarkdownTextSplitter to handle the structure.
            vector_store.add_filing_section(
                ticker=job.ticker,
                accession_number=target_filing.accession_no,
                section_name="Full Report",
                content=content,
                metadata={
                    "year": job.year,
                    "form_type": job.form_type,
                    "filing_date": str(target_filing.filing_date),
                }
            )

            # 5. Success
            job.status = JobStatus.DONE
            job.accession_no = target_filing.accession_no
            session.add(job)
            session.commit()
            logger.info("Ingestion complete", job_id=job_id)

        except Exception as e:
            logger.exception("Ingestion failed", job_id=job_id, error=str(e))
            job.status = JobStatus.FAILED
            job.error_msg = str(e)
            session.add(job)
            session.commit()
