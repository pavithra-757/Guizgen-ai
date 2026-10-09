import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from database.db import reset_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    reset_db()

def test_student_quiz_submission_and_evaluation():
    # 1. Setup Faculty & Approved Published Quiz
    fac_resp = client.post("/api/auth/register", json={
        "name": "Prof. Ada Lovelace",
        "email": "ada@quizgen.edu",
        "password": "Password123!",
        "role": "faculty"
    })
    fac_token = fac_resp.json()["access_token"]
    fac_headers = {"Authorization": f"Bearer {fac_token}"}

    gen_resp = client.post("/api/quizzes/generate", json={
        "title": "Database Systems",
        "topic": "SQL & Normalization",
        "difficulty": "Easy",
        "num_questions": 3,
        "question_types": ["mcq", "tf"]
    }, headers=fac_headers)
    quiz_id = gen_resp.json()["quiz_id"]
    questions = gen_resp.json()["questions"]

    # Approve & Publish Quiz
    client.post(f"/api/quizzes/{quiz_id}/approve", headers=fac_headers)
    client.post(f"/api/quizzes/{quiz_id}/publish", headers=fac_headers)

    # 2. Register Student
    stu_resp = client.post("/api/auth/register", json={
        "name": "Student Bob",
        "email": "bob@student.edu",
        "password": "Password123!",
        "role": "student"
    })
    stu_token = stu_resp.json()["access_token"]
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    # 3. Student Lists Published Quizzes
    list_resp = client.get("/api/quizzes/published/list", headers=stu_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["quizzes"]) >= 1

    # 4. Student Submits Answers
    answers_payload = {
        str(questions[0]["id"]): questions[0]["correct_answer"],
        str(questions[1]["id"]): questions[1]["correct_answer"],
        str(questions[2]["id"]): "Wrong Answer"
    }

    sub_resp = client.post(f"/api/quizzes/{quiz_id}/submit", json={"answers": answers_payload}, headers=stu_headers)
    assert sub_resp.status_code == 200
    res_data = sub_resp.json()
    
    assert res_data["score"] == 2.0
    assert res_data["max_score"] == 3.0
    assert res_data["percentage"] == 66.67
    assert len(res_data["breakdown"]) == 3
