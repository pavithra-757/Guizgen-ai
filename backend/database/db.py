import sqlite3
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent.parent / "quizgen.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('faculty', 'student')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Quizzes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        num_questions INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending_approval' CHECK(status IN ('draft', 'pending_approval', 'approved', 'published', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(created_by) REFERENCES users(id)
    );
    """)

    # Questions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        question_type TEXT NOT NULL CHECK(question_type IN ('mcq', 'tf', 'short_answer')),
        options TEXT, -- JSON string array
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        subtopic TEXT,
        quality_score REAL DEFAULT 1.0,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'flagged', 'edited')),
        feedback_notes TEXT,
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    """)

    # Submissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        score REAL DEFAULT 0,
        max_score REAL DEFAULT 0,
        percentage REAL DEFAULT 0,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id),
        FOREIGN KEY(student_id) REFERENCES users(id)
    );
    """)

    # Submission Answers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submission_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        student_answer TEXT,
        is_correct INTEGER DEFAULT 0,
        points_awarded REAL DEFAULT 0,
        max_points REAL DEFAULT 1,
        feedback TEXT,
        FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
        FOREIGN KEY(question_id) REFERENCES questions(id)
    );
    """)

    # Weak Area Reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weak_area_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        quiz_id INTEGER NOT NULL,
        weak_topics TEXT, -- JSON array
        strengths TEXT, -- JSON array
        recommendations TEXT, -- JSON array
        status TEXT DEFAULT 'generated' CHECK(status IN ('generated', 'faculty_approved')),
        faculty_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
        FOREIGN KEY(student_id) REFERENCES users(id),
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
    );
    """)

    conn.commit()
    conn.close()

def reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DROP TABLE IF EXISTS weak_area_reports;")
    cursor.execute("DROP TABLE IF EXISTS submission_answers;")
    cursor.execute("DROP TABLE IF EXISTS submissions;")
    cursor.execute("DROP TABLE IF EXISTS questions;")
    cursor.execute("DROP TABLE IF EXISTS quizzes;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()
    init_db()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
