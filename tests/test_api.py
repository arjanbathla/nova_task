import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app, get_db_engine
from app.db import get_engine, init_db, get_session
from app.models import Application


@pytest.fixture
def test_db_engine():
    """Create a test database engine using in-memory SQLite."""
    from sqlalchemy import create_engine
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
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


def test_root_returns_200_with_form(client):
    """GET / returns 200 and contains a form"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"<form" in response.content


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
        "pre_existing_conditions": False
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
        assert application.pre_existing_conditions is False
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
        # SQLite returns naive datetimes, so convert before/after to naive for comparison
        assert before.replace(tzinfo=None) <= application.created_at <= after.replace(tzinfo=None) + timedelta(seconds=1)
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


def test_get_existing_application_returns_200(client):
    """Existing application returns 200 with all fields matching what was saved"""
    # First, create an application
    post_response = client.post("/applications", json={
        "name": "Sarah Connor",
        "age": 35,
        "smoker": False,
        "coverage_amount": 200000,
        "occupation": "medium_risk",
        "pre_existing_conditions": False
    })
    assert post_response.status_code == 201
    post_data = post_response.json()
    application_id = post_data["application_id"]
    
    # Now retrieve it
    get_response = client.get(f"/applications/{application_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    
    # Verify all fields match the POST response
    assert get_data["application_id"] == post_data["application_id"]
    assert get_data["status"] == post_data["status"]
    assert get_data["quote"] == post_data["quote"]
    assert get_data["breakdown"] == post_data["breakdown"]
    assert get_data["reason"] == post_data["reason"]
    assert get_data["submitted_at"] == post_data["submitted_at"]


def test_get_nonexistent_uuid_returns_404(client):
    """Non-existent UUID returns 404"""
    import uuid
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/applications/{random_uuid}")
    assert response.status_code == 404


def test_get_invalid_uuid_format_returns_422(client):
    """Invalid UUID format returns 422"""
    response = client.get("/applications/not-a-uuid")
    assert response.status_code == 422


def test_conditions_true_with_medical_details_returns_201_referred(client, test_db_engine):
    """Pre-existing conditions with medical details returns 201, status referred, and saves details"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": True,
        "medical_details": "Diabetes type 2, controlled with medication"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "referred"
    application_id = data["application_id"]
    
    # Verify medical_details is saved in database
    session = get_session(test_db_engine)
    try:
        application = session.query(Application).filter_by(id=application_id).first()
        assert application.medical_details == "Diabetes type 2, controlled with medication"
    finally:
        session.close()


def test_conditions_true_without_medical_details_returns_422(client):
    """Pre-existing conditions without medical details returns 422"""
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": True
    })
    assert response.status_code == 422


def test_conditions_false_without_medical_details_returns_201(client):
    """No pre-existing conditions and no medical details returns 201"""
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
    assert data["status"] == "approved"


def test_medical_details_over_1000_characters_returns_422(client):
    """Medical details over 1000 characters returns 422"""
    long_details = "A" * 1001
    response = client.post("/applications", json={
        "name": "John Smith",
        "age": 25,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": True,
        "medical_details": long_details
    })
    assert response.status_code == 422
