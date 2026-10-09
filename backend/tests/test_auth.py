import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from database.db import reset_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    reset_db()

def test_user_registration_and_login():
    # 1. Register Faculty User
    faculty_email = "test_faculty@quizgen.edu"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Dr. Sarah Smith",
        "email": faculty_email,
        "password": "Password123!",
        "role": "faculty"
    })
    assert reg_resp.status_code == 200, reg_resp.text
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "faculty"

    # 2. Duplicate Registration Rejection
    dup_resp = client.post("/api/auth/register", json={
        "name": "Dr. Sarah Smith",
        "email": faculty_email,
        "password": "Password123!",
        "role": "faculty"
    })
    assert dup_resp.status_code == 400

    # 3. Login
    login_resp = client.post("/api/auth/login", json={
        "email": faculty_email,
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 4. Verify /me endpoint
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["email"] == faculty_email
