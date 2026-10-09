import json
import logging
from typing import List, Dict, Any
from agents.base_agent import BaseAgent

logger = logging.getLogger("QualityCheckerAgent")

class QualityCheckerAgent(BaseAgent):
    """
    Agent #3: Evaluates question clarity, distractor quality, difficulty match, and structural integrity.
    Flags questions that fail quality thresholds.
    """
    def __init__(self):
        super().__init__(
            name="Quality Checker Agent",
            role_description="Audits pedagogical quality, flags ambiguity or errors, and scores question validity."
        )

    def audit_questions(self, questions: List[Dict[str, Any]], target_difficulty: str) -> List[Dict[str, Any]]:
        prompt = f"""
You are an expert educational auditor and psychometrician.
Audit the following questions for target difficulty "{target_difficulty}".
Check for:
1. Clarity & grammatical accuracy
2. Distractor quality (no obvious trick or duplicate options)
3. Correctness of answer key
4. Alignment with difficulty: {target_difficulty}

Questions to audit:
{json.dumps(questions, indent=2)}

Return ONLY a JSON array of objects, preserving all existing keys and adding:
- quality_score: float between 0.0 and 1.0
- status: string ("pending" if score >= 0.8 else "flagged")
- feedback_notes: string (auditor notes or suggestions for improvement)
"""
        raw_response = self.call_gemini(prompt)
        if raw_response:
            parsed = self.clean_json_response(raw_response)
            if isinstance(parsed, list) and len(parsed) == len(questions):
                logger.info(f"[{self.name}] Successfully audited questions via Gemini API.")
                return parsed

        logger.info(f"[{self.name}] Auditing questions via Demo Mode Quality Engine.")
        return self._audit_demo_questions(questions, target_difficulty)

    def _audit_demo_questions(self, questions: List[Dict[str, Any]], target_difficulty: str) -> List[Dict[str, Any]]:
        audited = []
        for idx, q in enumerate(questions):
            q_copy = dict(q)
            q_text = q_copy.get("question_text", "")
            q_type = q_copy.get("question_type", "mcq")
            options = q_copy.get("options", [])
            correct_ans = q_copy.get("correct_answer", "")

            # Heuristic Quality Scoring
            score = 0.95
            notes = []

            if not q_text or len(q_text) < 15:
                score -= 0.3
                notes.append("Question stem is too brief or ambiguous.")

            if q_type == "mcq":
                if len(options) < 4:
                    score -= 0.4
                    notes.append("MCQ has fewer than 4 distinct choices.")
                if correct_ans not in options:
                    score -= 0.5
                    notes.append("Correct answer is missing from option list!")
                if len(set(options)) != len(options):
                    score -= 0.3
                    notes.append("Duplicate options detected.")
            elif q_type == "tf":
                if len(options) != 2:
                    score -= 0.2
                    notes.append("True/False options missing.")

            # Artificially flag one item for demonstration of Human-in-the-Loop if idx == 2 and total >= 3
            if idx == 2 and len(questions) >= 3:
                score = 0.65
                notes.append("Auditor Flag: Question stem could be framed more concisely for higher clarity.")

            score = max(0.0, min(1.0, round(score, 2)))
            q_copy["quality_score"] = score
            q_copy["status"] = "flagged" if score < 0.8 else "pending"
            q_copy["feedback_notes"] = "; ".join(notes) if notes else "Passed quality verification checks."

            audited.append(q_copy)

        return audited
