"""SQLModel ORM models for background processing jobs."""
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    """States a background ingestion job can be in."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class ProcessingJob(SQLModel, table=True):
    """Track background ingestion jobs."""
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    accession_no: str = Field(index=True)
    form_type: str
    year: int
    status: JobStatus = Field(default=JobStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error_msg: str | None = None
