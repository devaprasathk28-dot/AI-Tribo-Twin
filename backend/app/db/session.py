from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATABASE_URL


def make_engine(database_url: str | None = None):
    url = database_url or DATABASE_URL
    options: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **options)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
