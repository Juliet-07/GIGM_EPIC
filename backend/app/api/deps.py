from datetime import datetime
from typing import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from app.timeutil import utcnow


def get_db(request: Request) -> Iterator[Session]:
    db = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()


def get_now() -> datetime:
    return utcnow()