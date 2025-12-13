"""Database engine and session helpers for the API."""
import os
from collections.abc import Generator
from sqlmodel import Session, SQLModel, create_engine

from src.config import settings

# Create engine
# check_same_thread=False is needed for SQLite with FastAPI
engine = create_engine(
    f"sqlite:///{settings.sqlite_db_path}",
    connect_args={"check_same_thread": False},
    echo=True if settings.log_level == "DEBUG" else False
)


def init_db() -> None:
    """Create tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session
