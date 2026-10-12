from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_valid_application_returns_201():
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


def test_age_17_returns_422():
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


def test_age_81_returns_422():
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


def test_coverage_40000_returns_422():
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


def test_coverage_1100000_returns_422():
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


def test_coverage_not_multiple_of_10000_returns_422():
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


def test_missing_name_returns_422():
    """Missing required field returns 422 validation error"""
    response = client.post("/applications", json={
        "age": 25,
        "smoker": False,
        "coverage_amount": 100000,
        "occupation": "low_risk",
        "pre_existing_conditions": False
    })
    assert response.status_code == 422


def test_invalid_occupation_returns_422():
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


def test_referred_case_returns_201():
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


def test_declined_case_returns_201():
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
