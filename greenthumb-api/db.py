"""Database session factory for the cloud greenthumb-api.

Reads ``DATABASE_URL`` from the environment (set in compose.yaml / k8s secrets)
and exposes:
  - ``get_session()`` — FastAPI dependency that yields a SQLModel session.
  - ``create_db_and_tables()`` — idempotent DDL creation (called in lifespan).
"""
from __future__ import annotations

import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ["DATABASE_URL"]   # Fail fast if not set

_engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Create all tables defined in greenthumb_models (idempotent)."""
    SQLModel.metadata.create_all(_engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session for the duration of the request."""
    with Session(_engine) as session:
        yield session
