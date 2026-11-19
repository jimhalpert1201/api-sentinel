import uuid
from datetime import UTC, datetime

from app.auth.jwt import create_access_token
from app.models.incident import Incident, IncidentEvent
from app.models.monitor import Monitor
from app.models.user import User


def setup_user_with_incident(db_session, email="owner@example.com", username="owner"):
    user = User(email=email, username=username, hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    monitor = Monitor(user_id=user.id, name="Test Mon", url="https://api.test.com")
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)

    now = datetime.now(UTC)
    incident = Incident(
        monitor_id=monitor.id,
        status="open",
        cause="consecutive_failures",
        started_at=now,
        description="Monitor failed 3 consecutive checks.",
    )
    db_session.add(incident)
    db_session.flush()

    event = IncidentEvent(
        incident_id=incident.id,
        event_type="incident_created",
        description="Incident created.",
        created_at=now,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(incident)

    return user, monitor, incident, event


def test_list_incidents(client, db_session):
    """Verify listing incidents for authenticated user."""
    user, _monitor, incident, _event = setup_user_with_incident(db_session)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/incidents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(incident.id)
    assert data[0]["status"] == "open"
    assert data[0]["cause"] == "consecutive_failures"


def test_list_incidents_status_filter(client, db_session):
    """Verify filtering incidents by status query param."""
    user, _monitor, _incident, _event = setup_user_with_incident(db_session)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Query status=open
    resp_open = client.get("/api/v1/incidents?status=open", headers=headers)
    assert resp_open.status_code == 200
    assert len(resp_open.json()) == 1

    # Query status=resolved (should be empty)
    resp_resolved = client.get("/api/v1/incidents?status=resolved", headers=headers)
    assert resp_resolved.status_code == 200
    assert len(resp_resolved.json()) == 0


def test_get_incident_detail(client, db_session):
    """Verify getting single incident detail with nested events."""
    user, monitor, incident, _event = setup_user_with_incident(db_session)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/v1/incidents/{incident.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(incident.id)
    assert data["monitor_id"] == str(monitor.id)
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "incident_created"


def test_get_incident_events_timeline(client, db_session):
    """Verify GET /incidents/{id}/events returns timeline of events."""
    user, _monitor, incident, _event = setup_user_with_incident(db_session)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/v1/incidents/{incident.id}/events", headers=headers)
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "incident_created"
    assert events[0]["incident_id"] == str(incident.id)


def test_acknowledge_incident(client, db_session):
    """Verify acknowledging an incident updates status to acknowledged and creates event."""
    user, _monitor, incident, _event = setup_user_with_incident(db_session)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.patch(f"/api/v1/incidents/{incident.id}/acknowledge", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_at"] is not None

    # Check via standard PATCH /incidents/{id} as well
    resp_standard = client.patch(
        f"/api/v1/incidents/{incident.id}",
        json={"status": "acknowledged"},
        headers=headers,
    )
    assert resp_standard.status_code == 200

    # Verify event logged in DB
    timeline = client.get(f"/api/v1/incidents/{incident.id}/events", headers=headers).json()
    assert len(timeline) == 2
    types = [e["event_type"] for e in timeline]
    assert "incident_acknowledged" in types


def test_incident_multi_tenant_isolation(client, db_session):
    """Verify user B cannot view or acknowledge user A's incident."""
    _user_a, _monitor_a, incident_a, _event_a = setup_user_with_incident(
        db_session,
        email="a@example.com",
        username="a",
    )
    user_b = User(email="b@example.com", username="b", hashed_password="pw")
    db_session.add(user_b)
    db_session.commit()

    token_b = create_access_token(user_id=user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B list incidents (should not see A's incident)
    resp_list = client.get("/api/v1/incidents", headers=headers_b)
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 0

    # User B get incident detail (404)
    resp_get = client.get(f"/api/v1/incidents/{incident_a.id}", headers=headers_b)
    assert resp_get.status_code == 404
    assert resp_get.json()["detail"] == "Incident not found"

    # User B get timeline events (404)
    resp_events = client.get(f"/api/v1/incidents/{incident_a.id}/events", headers=headers_b)
    assert resp_events.status_code == 404

    # User B acknowledge (404)
    resp_ack = client.patch(f"/api/v1/incidents/{incident_a.id}/acknowledge", headers=headers_b)
    assert resp_ack.status_code == 404


def test_incidents_unauthenticated(client):
    """Verify unauthenticated requests return 401."""
    random_id = uuid.uuid4()
    assert client.get("/api/v1/incidents").status_code == 401
    assert client.get(f"/api/v1/incidents/{random_id}").status_code == 401
    assert client.get(f"/api/v1/incidents/{random_id}/events").status_code == 401
    assert client.patch(f"/api/v1/incidents/{random_id}").status_code == 401
