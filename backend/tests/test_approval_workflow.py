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

def test_human_in_the_loop_approval_and_publishing_gate():
    # 1. Register Faculty
    reg_resp = client.post("/api/auth/register", json={
        "name": "Prof. Alan Turing",
        "email": "turing@quizgen.edu",
        "password": "Password123!",
        "role": "faculty"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Generate Quiz (Status: pending_approval)
    gen_resp = client.post("/api/quizzes/generate", json={
        "title": "Algorithms 101",
        "topic": "Sorting & Searching",
        "difficulty": "Medium",
        "num_questions": 3,
        "question_types": ["mcq", "tf"]
    }, headers=headers)
    assert gen_resp.status_code == 200
    quiz_id = gen_resp.json()["quiz_id"]

    # 3. Attempt to Publish Quiz BEFORE Faculty Approval -> MUST FAIL with 400!
    pub_fail_resp = client.post(f"/api/quizzes/{quiz_id}/publish", headers=headers)
    assert pub_fail_resp.status_code == 400
    assert "must explicitly approve" in pub_fail_resp.json()["detail"]

    # 4. Faculty Edit Question
    questions = gen_resp.json()["questions"]
    first_q_id = questions[0]["id"]
    edit_resp = client.put(f"/api/quizzes/{quiz_id}/questions/{first_q_id}", json={
        "question_text": "Updated Stem: What is the worst-case time complexity of QuickSort?",
        "correct_answer": "O(n^2)",
        "explanation": "QuickSort degrades to O(n^2) when poor pivot choices are made consistently."
    }, headers=headers)
    assert edit_resp.status_code == 200
    assert edit_resp.json()["question"]["status"] == "edited"

    # 5. Faculty Approves Quiz
    app_resp = client.post(f"/api/quizzes/{quiz_id}/approve", headers=headers)
    assert app_resp.status_code == 200

    # 6. Attempt Publish AFTER Faculty Approval -> MUST SUCCEED!
    pub_success_resp = client.post(f"/api/quizzes/{quiz_id}/publish", headers=headers)
    assert pub_success_resp.status_code == 200
    assert pub_success_resp.json()["status"] == "published"
