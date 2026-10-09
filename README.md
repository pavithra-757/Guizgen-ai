# AI-Powered Automatic Quiz Generator Agent with Human-in-the-Loop

An end-to-end, multi-agent AI assessment platform built with **Python FastAPI**, **Google Gemini AI**, **SQLite**, and modern **HTML/CSS/JavaScript**.

This platform automates quiz generation, answer key creation, pedagogical quality checking, auto-grading, and weak-area analysis while keeping faculty in control through a strict **Human-in-the-Loop approval gate**.

---

## 🌟 Key Features

1. **7-Agent Autonomous Architecture**:
   - **Quiz Generator Agent**: Generates question stems, options, and subtopic mappings.
   - **Answer Key Agent**: Generates canonical answers, step-by-step explanations, and scoring rubrics.
   - **Quality Checker Agent**: Audits question clarity, distractor quality, difficulty match, and flags ambiguous items.
   - **Human Approval Agent**: Enforces faculty approval rules and guards the publishing gate. Unapproved quizzes **cannot** be published.
   - **Evaluation Agent**: Auto-evaluates student submissions (exact match for MCQ/TF, semantic scoring for short answers).
   - **Weak Area Analyzer Agent**: Detects knowledge gaps (<70% accuracy), categorizes subtopic mastery, and crafts personalized study plans.
   - **Central Agent Orchestrator**: Coordinates multi-agent pipelines and handles graceful fallback to **Smart Demo Mode** if Gemini API key is unconfigured.

2. **Role-Based Access Control**:
   - **Faculty Portal**: Create AI quizzes, review/edit generated questions, inspect auditor quality scores, approve quizzes, publish to students, and sign off on weak-area reports.
   - **Student Hub**: Browse published quizzes, complete interactive timed attempts, view instant auto-graded results, and receive AI remedial learning plans.

3. **Smart Demo Mode Fallback**:
   - Operates 100% reliably out of the box even without a `GEMINI_API_KEY`. When a valid key is provided in `.env`, it automatically connects to Google Gemini 2.5 Flash API.

---

## 📁 Project Directory Structure

```
quizgen-ai/
├── frontend/
│   ├── index.html        # Single-page application UI (Home, Dashboards, Quiz Creator, Taking, Results)
│   ├── style.css         # Navy-Blue & Violet modern responsive theme
│   └── script.js         # State management, API integration, and agent progress visualizer
├── backend/
│   ├── main.py           # FastAPI entry point & static mounts
│   ├── requirements.txt  # Python backend dependencies
│   ├── quizgen.db        # SQLite database (auto-created on startup)
│   ├── venv/             # Python virtual environment
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Gemini API client & Demo Mode handler
│   │   ├── generator_agent.py        # Agent #1: Quiz Question Generator
│   │   ├── answer_key_agent.py       # Agent #2: Canonical Answer Key Generator
│   │   ├── quality_checker_agent.py  # Agent #3: Quality Auditor & Flagging Engine
│   │   ├── human_approval_agent.py   # Agent #4: Human-in-the-Loop Gatekeeper
│   │   ├── evaluator_agent.py        # Agent #5: Student Submission Auto-Grader
│   │   ├── weak_area_analyzer_agent.py # Agent #6: Subtopic Gap & Study Plan Analyzer
│   │   └── orchestrator.py           # Agent #7: Central Pipeline Orchestrator
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py        # Registration, Login, JWT authentication
│   │   ├── quizzes.py     # Quiz generation, editing, approval, publishing
│   │   ├── submissions.py # Student quiz attempt submissions & grading
│   │   └── reports.py     # Weak area reports & faculty signoff
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py          # SQLite database schema, connections & reset helpers
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py               # Authentication & token tests
│       ├── test_quiz_generator.py     # Multi-agent generation pipeline tests
│       ├── test_approval_workflow.py  # Human-in-the-Loop & publishing guard tests
│       ├── test_student_submission.py # Student attempt & grading tests
│       └── test_weak_area_analysis.py # Weak area analyzer & report signoff tests
├── .env.example
├── .env
├── .gitignore
└── README.md
```

---

## 🛠️ Step-by-Step Windows Installation & Setup Guide

### Step 1: Open Terminal in Project Directory
Open PowerShell or Command Prompt and navigate to the project directory:
```powershell
cd c:\Users\nprhp\Downloads\quizgen-ai
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv backend/venv
.\backend\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
To use Google Gemini API, edit `.env` and add your key:
```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
SECRET_KEY=quizgen_ai_secret_key_2026_super_secure_random
PORT=8000
```
*Note: If `GEMINI_API_KEY` is omitted, the application automatically runs in Smart Demo Mode.*

### Step 5: Initialize Database
```powershell
$env:PYTHONPATH='backend'
python backend/database/db.py
```

---

## 🧪 Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
$env:PYTHONPATH='backend'
backend/venv/Scripts/pytest backend/tests/
```

Expected output:
```
======================== 6 passed in 8.44s ========================
```

---

## 🚀 Running the Application

Start the FastAPI server (which serves both the REST API and the Frontend UI):

```powershell
$env:PYTHONPATH='backend'
backend/venv/Scripts/python backend/main.py
```

### 📍 Local Application URLs:
- **Frontend User Interface**: [http://localhost:8000/](http://localhost:8000/)
- **API Health & AI Engine Status**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Interactive Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative OpenAPI Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 💡 Troubleshooting Common Issues

1. **Import Error when running tests or main script**:
   - Make sure `PYTHONPATH` is set to `backend` before launching commands: `$env:PYTHONPATH='backend'`
2. **Execution Policy Error in PowerShell (`Activate.ps1 cannot be loaded`)**:
   - Run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
3. **Port 8000 is already in use**:
   - Change `PORT=8005` in `.env` and re-run `python backend/main.py`.

---

## 📜 License
MIT License — Free for educational and research use.
# Guizgen-ai
