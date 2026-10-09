import json
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.db import get_db_connection
from agents.orchestrator import CentralAgentOrchestrator
from api.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Submissions"])
orchestrator = CentralAgentOrchestrator()

class SubmitAnswersSchema(BaseModel):
    answers: Dict[int, str] # {question_id: student_answer_string}

@router.post("/quizzes/{quiz_id}/submit")
def submit_quiz(quiz_id: int, data: SubmitAnswersSchema, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can submit quiz attempts.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz or quiz["status"] != "published":
        conn.close()
        raise HTTPException(status_code=400, detail="Quiz is not available for submission.")

    cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
    raw_questions = cursor.fetchall()
    if not raw_questions:
        conn.close()
        raise HTTPException(status_code=400, detail="Quiz has no questions.")

    questions = []
    for q in raw_questions:
        qd = dict(q)
        qd["options"] = json.loads(qd["options"]) if qd["options"] else []
        questions.append(qd)

    # Run Multi-Agent Evaluation & Weak Area Pipeline
    eval_pipeline_result = orchestrator.run_student_evaluation_pipeline(
        topic=quiz["topic"],
        questions=questions,
        student_answers=data.answers
    )

    # Store Submission Container
    cursor.execute("""
    INSERT INTO submissions (quiz_id, student_id, score, max_score, percentage)
    VALUES (?, ?, ?, ?, ?)
    """, (
        quiz_id,
        current_user["user_id"],
        eval_pipeline_result["score"],
        eval_pipeline_result["max_score"],
        eval_pipeline_result["percentage"]
    ))
    submission_id = cursor.lastrowid

    # Store Submission Answers
    for item in eval_pipeline_result["breakdown"]:
        cursor.execute("""
        INSERT INTO submission_answers (submission_id, question_id, student_answer, is_correct, points_awarded, max_points, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id,
            item["question_id"],
            item["student_answer"],
            item["is_correct"],
            item["points_awarded"],
            item["max_points"],
            item["feedback"]
        ))

    # Store Weak Area Report
    report = eval_pipeline_result["report"]
    cursor.execute("""
    INSERT INTO weak_area_reports (submission_id, student_id, quiz_id, weak_topics, strengths, recommendations, status)
    VALUES (?, ?, ?, ?, ?, ?, 'generated')
    """, (
        submission_id,
        current_user["user_id"],
        quiz_id,
        json.dumps(report["weak_topics"]),
        json.dumps(report["strengths"]),
        json.dumps(report["recommendations"])
    ))
    report_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "message": "Quiz submission evaluated successfully.",
        "submission_id": submission_id,
        "score": eval_pipeline_result["score"],
        "max_score": eval_pipeline_result["max_score"],
        "percentage": eval_pipeline_result["percentage"],
        "breakdown": eval_pipeline_result["breakdown"],
        "report_id": report_id,
        "report": report
    }

@router.get("/submissions/student/my-submissions")
def get_my_submissions(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT s.*, q.title as quiz_title, q.topic as quiz_topic, r.id as report_id, r.status as report_status
    FROM submissions s
    JOIN quizzes q ON s.quiz_id = q.id
    LEFT JOIN weak_area_reports r ON s.id = r.submission_id
    WHERE s.student_id = ?
    ORDER BY s.submitted_at DESC
    """, (current_user["user_id"],))

    submissions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"submissions": submissions}

@router.get("/submissions/{submission_id}")
def get_submission_detail(submission_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT s.*, q.title as quiz_title, q.topic as quiz_topic, u.name as student_name
    FROM submissions s
    JOIN quizzes q ON s.quiz_id = q.id
    JOIN users u ON s.student_id = u.id
    WHERE s.id = ?
    """, (submission_id,))
    sub = cursor.fetchone()
    if not sub:
        conn.close()
        raise HTTPException(status_code=404, detail="Submission not found.")

    sub_dict = dict(sub)

    # Get answer details
    cursor.execute("""
    SELECT sa.*, q.question_text, q.correct_answer, q.explanation, q.subtopic, q.question_type
    FROM submission_answers sa
    JOIN questions q ON sa.question_id = q.id
    WHERE sa.submission_id = ?
    """, (submission_id,))
    answers = [dict(r) for r in cursor.fetchall()]

    # Get Weak area report
    cursor.execute("SELECT * FROM weak_area_reports WHERE submission_id = ?", (submission_id,))
    report_row = cursor.fetchone()
    report = None
    if report_row:
        report = dict(report_row)
        report["weak_topics"] = json.loads(report["weak_topics"]) if report["weak_topics"] else []
        report["strengths"] = json.loads(report["strengths"]) if report["strengths"] else []
        report["recommendations"] = json.loads(report["recommendations"]) if report["recommendations"] else []

    conn.close()
    return {
        "submission": sub_dict,
        "answers": answers,
        "report": report
    }
