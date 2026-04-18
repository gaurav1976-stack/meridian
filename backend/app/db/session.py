"""Single engine + session factory. Override `DATABASE_URL` in tests via env."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _normalize_db_url(url: str) -> str:
    """Pin Postgres URLs to the psycopg (v3) driver.

    Render's managed Postgres (and Heroku, and many PaaS providers) emit
    connection strings as `postgres://...` or `postgresql://...`. SQLAlchemy
    treats both as aliases for the legacy `psycopg2` DBAPI, which is not
    installed — this project ships `psycopg>=3.2` (psycopg v3) instead.
    Rewriting the scheme to `postgresql+psycopg://` at import time keeps the
    rest of the stack driver-agnostic.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


_database_url = _normalize_db_url(settings.database_url)

_connect_args: dict = {}
if _database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    _database_url,
    echo=False,
    future=True,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
