"""
SQLAlchemy engine and session factory.

The engine and SessionLocal are created once at import time. HTTP handlers must
use the request-scoped get_db() dependency (Deploy 2) or always close any
SessionLocal() they open in a try/finally — otherwise PostgreSQL connections
stay idle in the pool and accumulate on the server.
"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

connect_args = {}
if DATABASE_URL.startswith("postgres"):
    connect_args = {"sslmode": "require"}

# Never call create_engine() inside a route or service — only here.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: one Session per request, always closed after the response.
    Routes not yet using Depends(get_db) still work; migrate them in Deploy 2.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
