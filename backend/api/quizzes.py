import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.db import get_db_connection
from agents.orchestrator import CentralAgentOrchestrator
from api.auth import get_current_user

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])
orchestrator = CentralAgentOrchestrator()

# Request Schemas
class GenerateQuizSchema(BaseModel):
    title: str
    topic: str
    difficulty: str = "Medium" # Easy, Medium, Hard
    num_questions: int = 5
    question_types: List[str] = ["mcq", "tf", "short_answer"]

class QuestionEditSchema(BaseModel):
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    subtopic: Optional[str] = None

@router.post("/generate")
def generate_quiz(data: GenerateQuizSchema, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty members can generate quizzes.")

    # Execute Multi-Agent Generation Pipeline
    pipeline_result = orchestrator.run_quiz_generation_pipeline(
        topic=data.topic,
        difficulty=data.difficulty,
        count=data.num_questions,
        question_types=data.question_types
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert quiz container (status: pending_approval)
    cursor.execute("""
    INSERT INTO quizzes (title, topic, difficulty, num_questions, created_by, status)
    VALUES (?, ?, ?, ?, ?, 'pending_approval')
    """, (data.title.strip(), data.topic.strip(), data.difficulty, data.num_questions, current_user["user_id"]))
    
    quiz_id = cursor.lastrowid

    # Insert individual questions
    stored_questions = []
    for q in pipeline_result["questions"]:
        options_json = json.dumps(q.get("options", []))
        cursor.execute("""
        INSERT INTO questions (quiz_id, question_text, question_type, options, correct_answer, explanation, subtopic, quality_score, status, feedback_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quiz_id,
            q.get("question_text"),
            q.get("question_type"),
            options_json,
            q.get("correct_answer"),
            q.get("explanation"),
            q.get("subtopic"),
            q.get("quality_score", 1.0),
            q.get("status", "pending"),
            q.get("feedback_notes")
        ))
        q_id = cursor.lastrowid
        q_item = dict(q)
        q_item["id"] = q_id
        q_item["quiz_id"] = quiz_id
        stored_questions.append(q_item)

    conn.commit()
    conn.close()

    return {
        "message": "AI Multi-Agent Quiz Generation completed.",
        "quiz_id": quiz_id,
        "title": data.title,
        "topic": data.topic,
        "difficulty": data.difficulty,
        "status": "pending_approval",
        "flagged_count": pipeline_result["flagged_count"],
        "questions": stored_questions
    }

@router.get("/")
def list_quizzes(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    if current_user.get("role") == "faculty":
        cursor.execute("""
        SELECT q.*, u.name as creator_name, COUNT(qs.id) as question_count
        FROM quizzes q
        LEFT JOIN users u ON q.created_by = u.id
        LEFT JOIN questions qs ON q.id = qs.quiz_id
        WHERE q.created_by = ?
        GROUP BY q.id
        ORDER BY q.created_at DESC
        """, (current_user["user_id"],))
    else:
        # Students see published quizzes only
        cursor.execute("""
        SELECT q.*, u.name as creator_name, COUNT(qs.id) as question_count
        FROM quizzes q
        LEFT JOIN users u ON q.created_by = u.id
        LEFT JOIN questions qs ON q.id = qs.quiz_id
        WHERE q.status = 'published'
        GROUP BY q.id
        ORDER BY q.created_at DESC
        """)

    quizzes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"quizzes": quizzes}

@router.get("/published/list")
def list_published_quizzes(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT q.*, u.name as creator_name, COUNT(qs.id) as question_count
    FROM quizzes q
    LEFT JOIN users u ON q.created_by = u.id
    LEFT JOIN questions qs ON q.id = qs.quiz_id
    WHERE q.status = 'published'
    GROUP BY q.id
    ORDER BY q.created_at DESC
    """)
    quizzes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"quizzes": quizzes}

@router.get("/{quiz_id}")
def get_quiz_detail(quiz_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT q.*, u.name as creator_name FROM quizzes q LEFT JOIN users u ON q.created_by = u.id WHERE q.id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz:
        conn.close()
        raise HTTPException(status_code=404, detail="Quiz not found.")

    cursor.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (quiz_id,))
    raw_questions = cursor.fetchall()
    conn.close()

    questions = []
    for q in raw_questions:
        q_dict = dict(q)
        q_dict["options"] = json.loads(q_dict["options"]) if q_dict["options"] else []
        questions.append(q_dict)

    quiz_dict = dict(quiz)
    quiz_dict["questions"] = questions
    return {"quiz": quiz_dict}

@router.put("/{quiz_id}/questions/{q_id}")
def edit_question(quiz_id: int, q_id: int, data: QuestionEditSchema, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can edit questions.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM questions WHERE id = ? AND quiz_id = ?", (q_id, quiz_id))
    q_row = cursor.fetchone()
    if not q_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found.")

    original = dict(q_row)
    original["options"] = json.loads(original["options"]) if original["options"] else []

    edited_dict = data.model_dump(exclude_unset=True)
    updated = orchestrator.human_approval.process_question_edit(original, edited_dict)

    cursor.execute("""
    UPDATE questions
    SET question_text = ?, options = ?, correct_answer = ?, explanation = ?, subtopic = ?, quality_score = ?, status = ?, feedback_notes = ?
    WHERE id = ?
    """, (
        updated["question_text"],
        json.dumps(updated["options"]),
        updated["correct_answer"],
        updated["explanation"],
        updated["subtopic"],
        updated["quality_score"],
        updated["status"],
        updated["feedback_notes"],
        q_id
    ))

    conn.commit()
    conn.close()

    return {"message": "Question updated by faculty successfully.", "question": updated}

@router.post("/{quiz_id}/questions/{q_id}/approve")
def approve_question(quiz_id: int, q_id: int, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can approve questions.")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE questions SET status = 'approved', quality_score = 1.0, feedback_notes = 'Approved by faculty.' WHERE id = ? AND quiz_id = ?", (q_id, quiz_id))
    conn.commit()
    conn.close()
    return {"message": f"Question {q_id} approved."}

@router.post("/{quiz_id}/approve")
def approve_quiz(quiz_id: int, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can approve quizzes.")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE quizzes SET status = 'approved', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (quiz_id,))
    # Also set pending questions to approved
    cursor.execute("UPDATE questions SET status = 'approved' WHERE quiz_id = ? AND status != 'edited'", (quiz_id,))
    conn.commit()
    conn.close()
    return {"message": "Quiz approved by faculty. It can now be published."}

@router.post("/{quiz_id}/publish")
def publish_quiz(quiz_id: int, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can publish quizzes.")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz:
        conn.close()
        raise HTTPException(status_code=404, detail="Quiz not found.")

    cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = [dict(r) for r in cursor.fetchall()]

    # Validate Human-in-the-Loop publishing authorization via Orchestrator / HumanApprovalAgent
    validation = orchestrator.validate_publishing(quiz["status"], questions)
    if not validation["allowed"]:
        conn.close()
        raise HTTPException(status_code=400, detail=validation["reason"])

    cursor.execute("UPDATE quizzes SET status = 'published', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (quiz_id,))
    conn.commit()
    conn.close()

    return {"message": "Quiz successfully published to students!", "quiz_id": quiz_id, "status": "published"}
