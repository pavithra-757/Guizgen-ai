import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.db import get_db_connection
from api.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Reports & Analytics"])

class ApproveReportSchema(BaseModel):
    faculty_notes: Optional[str] = ""

@router.get("/reports/faculty/pending")
def list_pending_reports(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can review weak area reports.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT r.*, u.name as student_name, u.email as student_email, q.title as quiz_title, q.topic as quiz_topic, s.score, s.max_score, s.percentage
    FROM weak_area_reports r
    JOIN users u ON r.student_id = u.id
    JOIN quizzes q ON r.quiz_id = q.id
    JOIN submissions s ON r.submission_id = s.id
    WHERE q.created_by = ?
    ORDER BY r.created_at DESC
    """, (current_user["user_id"],))

    rows = cursor.fetchall()
    reports = []
    for r in rows:
        rd = dict(r)
        rd["weak_topics"] = json.loads(rd["weak_topics"]) if rd["weak_topics"] else []
        rd["strengths"] = json.loads(rd["strengths"]) if rd["strengths"] else []
        rd["recommendations"] = json.loads(rd["recommendations"]) if rd["recommendations"] else []
        reports.append(rd)

    conn.close()
    return {"reports": reports}

@router.post("/reports/{report_id}/approve")
def approve_report(report_id: int, data: ApproveReportSchema, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can approve reports.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM weak_area_reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    if not report:
        conn.close()
        raise HTTPException(status_code=404, detail="Report not found.")

    cursor.execute("""
    UPDATE weak_area_reports
    SET status = 'faculty_approved', faculty_notes = ?
    WHERE id = ?
    """, (data.faculty_notes or "Approved by faculty.", report_id))

    conn.commit()
    conn.close()

    return {"message": "Weak area report approved by faculty.", "report_id": report_id, "status": "faculty_approved"}

@router.get("/analytics/faculty-summary")
def get_faculty_summary(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can view summary analytics.")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total quizzes created by faculty
    cursor.execute("SELECT COUNT(*) as count FROM quizzes WHERE created_by = ?", (current_user["user_id"],))
    total_quizzes = cursor.fetchone()["count"]

    # Total published quizzes
    cursor.execute("SELECT COUNT(*) as count FROM quizzes WHERE created_by = ? AND status = 'published'", (current_user["user_id"],))
    published_quizzes = cursor.fetchone()["count"]

    # Total student submissions on faculty quizzes
    cursor.execute("""
    SELECT COUNT(s.id) as count, AVG(s.percentage) as avg_score
    FROM submissions s
    JOIN quizzes q ON s.quiz_id = q.id
    WHERE q.created_by = ?
    """, (current_user["user_id"],))
    sub_row = cursor.fetchone()
    total_submissions = sub_row["count"] or 0
    avg_score = round(sub_row["avg_score"] or 0, 1)

    # Pending reports needing approval
    cursor.execute("""
    SELECT COUNT(r.id) as count
    FROM weak_area_reports r
    JOIN quizzes q ON r.quiz_id = q.id
    WHERE q.created_by = ? AND r.status = 'generated'
    """, (current_user["user_id"],))
    pending_reports = cursor.fetchone()["count"] or 0

    conn.close()

    return {
        "total_quizzes": total_quizzes,
        "published_quizzes": published_quizzes,
        "total_submissions": total_submissions,
        "avg_student_score": avg_score,
        "pending_reports_approval": pending_reports
    }
