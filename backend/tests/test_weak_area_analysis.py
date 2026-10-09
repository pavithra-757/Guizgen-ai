import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from database.db import reset_db
from agents.weak_area_analyzer_agent import WeakAreaAnalyzerAgent

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    reset_db()

def test_weak_area_analyzer_agent_logic():
    agent = WeakAreaAnalyzerAgent()
    breakdown = [
        {"subtopic": "Recursion", "is_correct": 0, "points_awarded": 0.0},
        {"subtopic": "Recursion", "is_correct": 0, "points_awarded": 0.0},
        {"subtopic": "Arrays & Lists", "is_correct": 1, "points_awarded": 1.0},
        {"subtopic": "Arrays & Lists", "is_correct": 1, "points_awarded": 1.0}
    ]
    report = agent.analyze_performance("Data Structures", 50.0, breakdown)
    
    assert len(report["weak_topics"]) >= 1
    assert report["weak_topics"][0]["subtopic"] == "Recursion"
    assert report["weak_topics"][0]["accuracy"] == 0.0
    assert len(report["strengths"]) >= 1
    assert report["strengths"][0]["subtopic"] == "Arrays & Lists"
    assert len(report["recommendations"]) >= 1

def test_faculty_weak_area_report_approval_api():
    # 1. Setup Faculty & Student
    fac_resp = client.post("/api/auth/register", json={
        "name": "Prof. Charles Babbage",
        "email": "babbage@quizgen.edu",
        "password": "Password123!",
        "role": "faculty"
    })
    fac_token = fac_resp.json()["access_token"]
    fac_headers = {"Authorization": f"Bearer {fac_token}"}

    stu_resp = client.post("/api/auth/register", json={
        "name": "Student Alice",
        "email": "alice@student.edu",
        "password": "Password123!",
        "role": "student"
    })
    stu_token = stu_resp.json()["access_token"]
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    # 2. Faculty creates & publishes quiz
    gen_resp = client.post("/api/quizzes/generate", json={
        "title": "Computer Networks",
        "topic": "TCP/IP Protocol Stack",
        "difficulty": "Hard",
        "num_questions": 2,
        "question_types": ["mcq"]
    }, headers=fac_headers)
    quiz_id = gen_resp.json()["quiz_id"]
    questions = gen_resp.json()["questions"]

    client.post(f"/api/quizzes/{quiz_id}/approve", headers=fac_headers)
    client.post(f"/api/quizzes/{quiz_id}/publish", headers=fac_headers)

    # 3. Student submits quiz
    sub_resp = client.post(f"/api/quizzes/{quiz_id}/submit", json={
        "answers": {str(questions[0]["id"]): "Wrong Answer"}
    }, headers=stu_headers)
    report_id = sub_resp.json()["report_id"]

    # 4. Faculty lists pending reports
    rep_list_resp = client.get("/api/reports/faculty/pending", headers=fac_headers)
    assert rep_list_resp.status_code == 200
    assert len(rep_list_resp.json()["reports"]) >= 1

    # 5. Faculty approves weak area report
    app_resp = client.post(f"/api/reports/{report_id}/approve", json={
        "faculty_notes": "Reviewed by Prof. Babbage. Recommended student attend lab hour on TCP Handshake."
    }, headers=fac_headers)
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "faculty_approved"
