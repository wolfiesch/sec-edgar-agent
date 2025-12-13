"""Routes for triggering and monitoring ingestion jobs."""
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session # type: ignore

from src.api.middleware import verify_api_key
from src.api.models.requests import IngestRequest
from src.data.db import get_session
from src.data.db_models import JobStatus, ProcessingJob
from src.data.ingestion import ingest_filing

router = APIRouter()


@router.post("/", status_code=202)
async def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    _api_key: str = Depends(verify_api_key),
) -> dict[str, Any]:
    """
    Start robust background ingestion.
    """
    # Create Job
    job = ProcessingJob(
        ticker=request.ticker,
        form_type=request.form_type,
        year=request.year,
        status=JobStatus.PENDING,
        accession_no="PENDING",
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    if job.id is None:
         raise HTTPException(status_code=500, detail="Failed to create job ID")

    # Trigger Background Task
    background_tasks.add_task(ingest_filing, str(job.id))

    return {"job_id": job.id, "status": "PENDING"}


@router.get("/{job_id}")
async def get_ingestion_status(
    job_id: int,
    session: Session = Depends(get_session),
    _api_key: str = Depends(verify_api_key),
) -> ProcessingJob:
    """Fetch the status of a background ingestion job."""
    job = session.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
