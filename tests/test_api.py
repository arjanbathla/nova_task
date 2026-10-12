import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app, get_db_engine
from app.db import get_engine, init_db, get_session
from app.models import Application


@pytest.fixture
def test_db_engine():
    """Create a test database engine using in-memory SQLite."""
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(test_db_engine):
    """Create a test client with overridden database engine."""
    app.dependency_overrides[get_db_engine] = lambda: test_db_engine
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_valid_application_returns_201(client):
    """Valid application returns 201 with all required fields"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 201
    data = response.json()
    assert "application_id" in data
    assert data["status"] == "approved"
    assert data["quote"] == 500.00
    assert "breakdown" in data
    assert data["reason"] is None
    assert "submitted_at" in data


def test_age_17_returns_422(client):
    """Age below 18 returns 422 validation error"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 17,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_age_81_returns_422(client):
    """Age above 80 returns 422 validation error"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 81,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_coverage_40000_returns_422(client):
    """Coverage below 50000 returns 422 validation error"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 40000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_coverage_1100000_returns_422(client):
    """Coverage above 1000000 returns 422 validation error"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 1100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_coverage_not_multiple_of_10000_returns_422(client):
    """Coverage not multiple of 10000 returns 422 validation error"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 55000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_missing_name_returns_422(client):
    """Missing required field returns 422 validation error"""
    response = client.post("/applications", json={
        "age": 25,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_invalid_occupation_returns_422(client):
    """Invalid occupation value returns 422 validation error"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "invalid_occupation",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_referred_case_returns_201(client):
    """Referred case returns 201 with status and reason"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 66,
        "smoker": True,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": True
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "referred"
    assert data["quote"] is None
    assert data["reason"] is not None
    assert "breakdown" in data


def test_post_creates_record_in_database(client, test_db_engine):
    """POST creates record in temporary test database"""
    response = client.post("/applications", json={
        "name": "Jane Doe",
        "age": 30,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 201
    application_id = response.json()["application_id"]
    
    # Query database to verify record exists
    session = get_session(test_db_engine)
    try:
        application = session.query(Application).filter_by(id=application_id).first()
        assert application is not None
    finally:
        session.close()


def test_saved_application_has_all_fields(client, test_db_engine):
    """Saved application has all fields persisted correctly"""
    response = client.post("/applications", json={
        "name": "Bob Smith",
        "age": 45,
        "smoker": True,
        "coverage_amount": 250000,
        "occupation": "medium_risk",
        "pre_existing_conditions": True
    })
    assert response.status_code == 201
    application_id = response.json()["application_id"]
    
    # Query database and verify all fields
    session = get_session(test_db_engine)
    try:
        application = session.query(Application).filter_by(id=application_id).first()
        assert application.name == "Bob Smith"
        assert application.age == 45
        assert application.smoker is True
        assert application.coverage_amount == 250000
        assert application.occupation == "medium_risk"
        assert application.pre_existing_conditions is True
        assert application.status == "approved"
        assert application.quote is not None
        assert application.reason is None
    finally:
        session.close()


def test_application_id_is_uuid(client, test_db_engine):
    """Application ID is UUID and returned in response"""
    response = client.post("/applications", json={
        "name": "Alice Johnson",
        "age": 28,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 201
    application_id = response.json()["application_id"]
    
    # Verify it's a valid UUID format
    import uuid
    try:
        uuid.UUID(application_id)
    except ValueError:
        pytest.fail("application_id is not a valid UUID")
    
    # Verify it matches in database
    session = get_session(test_db_engine)
    try:
        application = session.query(Application).filter_by(id=application_id).first()
        assert application.id == application_id
    finally:
        session.close()


def test_timestamp_is_set_automatically(client, test_db_engine):
    """Timestamp is set automatically"""
    from datetime import datetime, timezone, timedelta
    
    before = datetime.now(timezone.utc)
    response = client.post("/applications", json={
        "name": "Charlie Brown",
        "age": 35,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    after = datetime.now(timezone.utc)
    
    assert response.status_code == 201
    application_id = response.json()["application_id"]
    
    # Query database and verify timestamp
    session = get_session(test_db_engine)
    try:
        application = session.query(Application).filter_by(id=application_id).first()
        assert application.created_at is not None
        # Verify timestamp is recent (within test execution window)
        assert before <= application.created_at <= after + timedelta(seconds=1)
    finally:
        session.close()


def test_declined_case_returns_201(client):
    """Declined case returns 201 with status and reason"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": True,
        "coverage_amount": 100000,
        "occupation": "high_risk",
        "pre_existing_conditions": True
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "declined"
    assert data["quote"] is None
    assert data["reason"] is not None
    assert "breakdown" in data
