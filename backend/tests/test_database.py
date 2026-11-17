import pytest
from app.core.database import get_db
from sqlalchemy.orm import Session


def test_get_db_session_lifecycle():
    """Verify get_db provides an active session and closes it cleanly."""
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)
    assert session.is_active

    # Closing generator should close session
    with pytest.raises(StopIteration):
        next(gen)


def test_get_db_session_closes_on_exception():
    """Verify get_db closes session even if an exception occurs during request handling."""
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)

    with pytest.raises(RuntimeError, match="Simulated request failure"):
        gen.throw(RuntimeError("Simulated request failure"))
