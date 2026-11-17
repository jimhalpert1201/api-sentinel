import uuid

import pytest
from app.models.check_result import CheckResult
from app.models.incident import Incident, IncidentEvent
from app.models.monitor import Monitor
from app.models.user import User
from sqlalchemy.exc import IntegrityError


def test_create_user(db_session):
    """Test user creation and default values."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw_example",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.role == "user"
    assert user.created_at is not None


def test_user_email_unique(db_session):
    """Test that email uniqueness is enforced."""
    u1 = User(email="unique@example.com", username="u1", hashed_password="pw")
    u2 = User(email="unique@example.com", username="u2", hashed_password="pw")
    db_session.add(u1)
    db_session.commit()

    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_create_monitor_and_cascade_delete(db_session):
    """Test monitor creation, relationships, and cascade deletion."""
    user = User(email="monitor_owner@example.com", username="owner", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    monitor = Monitor(
        user_id=user.id,
        name="Production API",
        url="https://api.example.com/health",
        http_method="GET",
        interval_seconds=60,
        timeout_seconds=30,
        expected_status_code=200,
    )
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)

    assert monitor.id is not None
    assert monitor.is_active is True

    # Add CheckResult
    check = CheckResult(
        monitor_id=monitor.id,
        status_code=200,
        response_time_ms=124.5,
        is_successful=True,
    )
    # Add Incident
    incident = Incident(
        monitor_id=monitor.id,
        status="open",
        cause="downtime",
    )
    db_session.add_all([check, incident])
    db_session.commit()
    db_session.refresh(incident)

    # Add IncidentEvent
    event = IncidentEvent(
        incident_id=incident.id,
        event_type="created",
        description="Monitor failed 3 consecutive health checks",
    )
    db_session.add(event)
    db_session.commit()

    # Verify associations
    assert db_session.query(CheckResult).filter_by(monitor_id=monitor.id).count() == 1
    assert db_session.query(Incident).filter_by(monitor_id=monitor.id).count() == 1
    assert db_session.query(IncidentEvent).filter_by(incident_id=incident.id).count() == 1
    assert check.monitor.name == "Production API"
    assert incident.events[0].event_type == "created"

    # Cascade delete monitor
    db_session.delete(monitor)
    db_session.commit()

    # Results, Incidents, and IncidentEvents must be deleted automatically
    assert db_session.query(CheckResult).filter_by(monitor_id=monitor.id).count() == 0
    assert db_session.query(Incident).filter_by(monitor_id=monitor.id).count() == 0
    assert db_session.query(IncidentEvent).filter_by(incident_id=incident.id).count() == 0
