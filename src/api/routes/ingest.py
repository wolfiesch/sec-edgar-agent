from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import Session

from src.api.models.requests import IngestRequest
from src.config import settings
from src.data.db import get_session
from src.data.db_models import JobStatus, ProcessingJob
from src.data.ingestion import ingest_filing

router = APIRouter()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != settings.api_key:
        raise HTTPException(
            status_code=403, detail="Could not validate credentials"
        )
    return api_key_header


@router.post("/", status_code=202)
async def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    api_key: str = Depends(get_api_key),
):
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

    # Trigger Background Task
    background_tasks.add_task(ingest_filing, job.id)

    return {"job_id": job.id, "status": "PENDING"}


@router.get("/{job_id}")
async def get_ingestion_status(
    job_id: int,
    session: Session = Depends(get_session),
    api_key: str = Depends(get_api_key),
):
    job = session.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
