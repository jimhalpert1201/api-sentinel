from datetime import UTC, datetime, timedelta

from app.models.check_result import CheckResult
from app.models.incident import Incident, IncidentEvent
from app.models.monitor import Monitor
from app.models.user import User
from app.services.incident_service import evaluate_monitor_incidents


def create_sample_monitor(db_session):
    user = User(email="inc_user@example.com", username="inc_user", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    monitor = Monitor(user_id=user.id, name="Test Monitor", url="https://api.test.com")
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)
    return monitor


def test_evaluate_under_threshold_failures(db_session):
    """Verify 1 or 2 consecutive failures do NOT open an incident when threshold is 3."""
    monitor = create_sample_monitor(db_session)
    now = datetime.now(UTC)

    # 2 failed checks
    for i in range(2):
        check = CheckResult(
            monitor_id=monitor.id,
            status_code=500,
            response_time_ms=100.0,
            is_successful=False,
            checked_at=now - timedelta(minutes=1 - i),
        )
        db_session.add(check)
        db_session.commit()

        incident = evaluate_monitor_incidents(db_session, monitor.id, check, threshold=3)
        assert incident is None

    # Assert no incidents exist
    incidents = db_session.query(Incident).filter_by(monitor_id=monitor.id).all()
    assert len(incidents) == 0


def test_evaluate_consecutive_failures_opens_incident(db_session):
    """Verify 3 consecutive failures open a new incident with an incident_created event."""
    monitor = create_sample_monitor(db_session)
    now = datetime.now(UTC)

    check = None
    for i in range(3):
        check = CheckResult(
            monitor_id=monitor.id,
            status_code=500,
            response_time_ms=100.0,
            is_successful=False,
            checked_at=now - timedelta(minutes=2 - i),
        )
        db_session.add(check)
        db_session.commit()

    incident = evaluate_monitor_incidents(db_session, monitor.id, check, threshold=3)
    assert incident is not None
    assert incident.status == "open"
    assert incident.cause == "consecutive_failures"
    assert incident.started_at is not None

    # Assert event was logged
    events = db_session.query(IncidentEvent).filter_by(incident_id=incident.id).all()
    assert len(events) == 1
    assert events[0].event_type == "incident_created"


def test_evaluate_consecutive_failures_idempotent(db_session):
    """Verify 4th consecutive failure does not create duplicate incident if one is already open."""
    monitor = create_sample_monitor(db_session)
    now = datetime.now(UTC)

    # Open an incident with 3 failures
    for i in range(3):
        c = CheckResult(
            monitor_id=monitor.id,
            status_code=500,
            response_time_ms=100.0,
            is_successful=False,
            checked_at=now - timedelta(minutes=3 - i),
        )
        db_session.add(c)
    db_session.commit()
    evaluate_monitor_incidents(db_session, monitor.id, c, threshold=3)

    # 4th failure
    c4 = CheckResult(
        monitor_id=monitor.id,
        status_code=500,
        response_time_ms=100.0,
        is_successful=False,
        checked_at=now,
    )
    db_session.add(c4)
    db_session.commit()

    evaluate_monitor_incidents(db_session, monitor.id, c4, threshold=3)

    all_incidents = db_session.query(Incident).filter_by(monitor_id=monitor.id).all()
    assert len(all_incidents) == 1


def test_evaluate_flapping_resets_counter(db_session):
    """Verify 2 fails, 1 success, then 1 fail does NOT open an incident."""
    monitor = create_sample_monitor(db_session)
    now = datetime.now(UTC)

    # Fail, Fail, Pass, Fail
    checks = [
        (False, 3),
        (False, 2),
        (True, 1),
        (False, 0),
    ]
    for is_succ, mins_ago in checks:
        c = CheckResult(
            monitor_id=monitor.id,
            status_code=200 if is_succ else 500,
            response_time_ms=50.0,
            is_successful=is_succ,
            checked_at=now - timedelta(minutes=mins_ago),
        )
        db_session.add(c)
        db_session.commit()
        evaluate_monitor_incidents(db_session, monitor.id, c, threshold=3)

    incidents = db_session.query(Incident).filter_by(monitor_id=monitor.id).all()
    assert len(incidents) == 0


def test_evaluate_auto_resolution(db_session):
    """Verify 3 consecutive successes auto-resolves open incident with incident_resolved event."""
    monitor = create_sample_monitor(db_session)
    now = datetime.now(UTC)

    # Open incident with 3 failures
    for i in range(3):
        c = CheckResult(
            monitor_id=monitor.id,
            status_code=500,
            response_time_ms=100.0,
            is_successful=False,
            checked_at=now - timedelta(minutes=6 - i),
        )
        db_session.add(c)
    db_session.commit()
    open_inc = evaluate_monitor_incidents(db_session, monitor.id, c, threshold=3)
    assert open_inc.status == "open"

    # 1st and 2nd success - should still be open
    for i in range(2):
        c_succ = CheckResult(
            monitor_id=monitor.id,
            status_code=200,
            response_time_ms=50.0,
            is_successful=True,
            checked_at=now - timedelta(minutes=3 - i),
        )
        db_session.add(c_succ)
        db_session.commit()
        inc = evaluate_monitor_incidents(db_session, monitor.id, c_succ, threshold=3)
        assert inc.status == "open"

    # 3rd success - should auto-resolve
    c_succ3 = CheckResult(
        monitor_id=monitor.id,
        status_code=200,
        response_time_ms=50.0,
        is_successful=True,
        checked_at=now,
    )
    db_session.add(c_succ3)
    db_session.commit()
    resolved_inc = evaluate_monitor_incidents(db_session, monitor.id, c_succ3, threshold=3)

    assert resolved_inc.status == "resolved"
    assert resolved_inc.resolved_at is not None

    events = db_session.query(IncidentEvent).filter_by(incident_id=resolved_inc.id).all()
    assert len(events) == 2
    event_types = [e.event_type for e in events]
    assert "incident_created" in event_types
    assert "incident_resolved" in event_types
