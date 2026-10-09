import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from database.db import init_db
from api import auth, quizzes, submissions, reports

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuizGenApp")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite Database...")
    init_db()
    logger.info("Database initialization complete.")
    yield

app = FastAPI(
    title="AI-Powered Automatic Quiz Generator Agent API",
    description="Multi-Agent Quiz Generation System with Human-in-the-Loop Approval",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(quizzes.router)
app.include_router(submissions.router)
app.include_router(reports.router)

# Health Check & AI System Status Endpoint
@app.get("/api/health")
def health_check():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    is_gemini_active = True if (api_key and api_key != "your_gemini_api_key_here") else False
    return {
        "status": "healthy",
        "app": "QuizGen AI Agent System",
        "ai_engine": "Google Gemini 2.5 Flash API" if is_gemini_active else "Smart Demo Mode AI",
        "gemini_api_configured": is_gemini_active
    }

# Mount Frontend static files at root
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
