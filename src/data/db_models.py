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


class ParsedTable(SQLModel, table=True):
    """Cached parsed table data."""
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    form_type: str = Field(index=True)
    year: int = Field(index=True)
    table_name: str = Field(index=True)

    # Content
    markdown: str
    structured_data_json: str  # Stored as JSON string
    citation_json: str # Stored as JSON string

    # Metadata
    source_method: str
    confidence: str

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
