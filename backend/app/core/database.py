"""
Database engine, session factory, and base model.

Usage:
    from app.core.database import get_db

    @router.get("/example")
    async def example(db: Session = Depends(get_db)):
        ...
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Create the SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,         # Maximum number of permanent connections
    max_overflow=20,      # Additional connections allowed beyond pool_size
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Session factory — creates new database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Yields a session and ensures it is closed after the request,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
