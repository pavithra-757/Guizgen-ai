import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from agents.orchestrator import CentralAgentOrchestrator

client = TestClient(app)

def test_multi_agent_quiz_generator_pipeline():
    orchestrator = CentralAgentOrchestrator()
    result = orchestrator.run_quiz_generation_pipeline(
        topic="Python Object Oriented Programming",
        difficulty="Medium",
        count=4,
        question_types=["mcq", "tf", "short_answer"]
    )

    assert result["topic"] == "Python Object Oriented Programming"
    assert len(result["questions"]) == 4
    
    # Check that each question has required keys from Generator, Answer Key, and Quality Checker agents
    for q in result["questions"]:
        assert "question_text" in q
        assert "question_type" in q
        assert "correct_answer" in q
        assert "explanation" in q
        assert "quality_score" in q
        assert "status" in q
        assert "subtopic" in q
