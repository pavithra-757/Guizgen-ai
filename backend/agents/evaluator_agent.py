import json
import logging
from typing import List, Dict, Any
from agents.base_agent import BaseAgent

logger = logging.getLogger("EvaluationAgent")

class EvaluationAgent(BaseAgent):
    """
    Agent #5: Automatically evaluates student responses against canonical answer keys.
    Handles exact matches for MCQ/TF and semantic evaluation for Short Answers.
    """
    def __init__(self):
        super().__init__(
            name="Evaluation Agent",
            role_description="Evaluates student responses, calculates exact and partial credit scores, and provides item feedback."
        )

    def evaluate_submission(
        self, questions: List[Dict[str, Any]], student_answers: Dict[int, str]
    ) -> Dict[str, Any]:
        """
        Evaluates a dictionary of {question_id: student_answer} against the question key objects.
        Returns detailed scoring breakdown.
        """
        total_max = len(questions)
        total_awarded = 0.0
        breakdown = []

        for q in questions:
            q_id = q.get("id")
            q_type = q.get("question_type", "mcq")
            correct_ans = str(q.get("correct_answer", "")).strip()
            student_ans = str(student_answers.get(q_id, "")).strip()

            is_correct = False
            points = 0.0
            feedback = ""

            if q_type in ["mcq", "tf"]:
                # Exact or case-insensitive string match
                if student_ans.lower() == correct_ans.lower():
                    is_correct = True
                    points = 1.0
                    feedback = "Correct! Excellent choice."
                else:
                    feedback = f"Incorrect. Standard answer: '{correct_ans}'. Explanation: {q.get('explanation', '')}"
            else: # short_answer
                eval_res = self._evaluate_short_answer(
                    q.get("question_text", ""), correct_ans, student_ans, q.get("explanation", "")
                )
                points = eval_res.get("score", 0.0)
                is_correct = points >= 0.7
                feedback = eval_res.get("feedback", "")

            total_awarded += points

            breakdown.append({
                "question_id": q_id,
                "question_text": q.get("question_text"),
                "subtopic": q.get("subtopic", "General"),
                "student_answer": student_ans,
                "correct_answer": correct_ans,
                "is_correct": 1 if is_correct else 0,
                "points_awarded": round(points, 2),
                "max_points": 1.0,
                "feedback": feedback
            })

        percentage = (total_awarded / total_max * 100) if total_max > 0 else 0.0

        return {
            "score": round(total_awarded, 2),
            "max_score": round(total_max, 2),
            "percentage": round(percentage, 2),
            "breakdown": breakdown
        }

    def _evaluate_short_answer(self, prompt_text: str, canonical_ans: str, student_ans: str, explanation: str) -> Dict[str, Any]:
        if not student_ans or len(student_ans.strip()) < 3:
            return {"score": 0.0, "feedback": "No answer or answer too brief."}

        prompt = f"""
Question: {prompt_text}
Expected Answer: {canonical_ans}
Explanation: {explanation}
Student Submission: {student_ans}

Grade the student's answer on a scale from 0.0 to 1.0 based on conceptual accuracy.
Return ONLY JSON:
{{
  "score": float between 0.0 and 1.0,
  "feedback": "Concise feedback for the student"
}}
"""
        raw_response = self.call_gemini(prompt)
        if raw_response:
            parsed = self.clean_json_response(raw_response)
            if "score" in parsed:
                return parsed

        # Fallback keyword match heuristics for Demo Mode
        student_words = set(student_ans.lower().split())
        canonical_words = set(canonical_ans.lower().split())
        overlap = len(student_words.intersection(canonical_words))
        
        if overlap >= 3 or ("static" in student_ans.lower() and "dynamic" in student_ans.lower()):
            return {"score": 1.0, "feedback": "Demonstrates clear conceptual understanding."}
        elif overlap >= 1:
            return {"score": 0.5, "feedback": "Partially correct. Lacks key specific technical terms."}
        else:
            return {"score": 0.0, "feedback": f"Incorrect concept. Expected reference to key principles in: {canonical_ans}"}
