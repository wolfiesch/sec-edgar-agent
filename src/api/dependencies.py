from fastapi import Depends
from sqlmodel import Session

from src.data.db import get_session


def get_db(session: Session = Depends(get_session)):
    """Yield database session."""
    return session
