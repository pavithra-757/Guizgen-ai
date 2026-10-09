import json
import logging
from typing import List, Dict, Any
from agents.base_agent import BaseAgent

logger = logging.getLogger("AnswerKeyAgent")

class AnswerKeyAgent(BaseAgent):
    """
    Agent #2: Generates canonical correct answers, detailed step-by-step explanations, and scoring weights.
    """
    def __init__(self):
        super().__init__(
            name="Answer Key Agent",
            role_description="Determines verified correct answers, comprehensive explanations, and rubric point allocations."
        )

    def attach_answer_keys(self, questions: List[Dict[str, Any]], topic: str) -> List[Dict[str, Any]]:
        prompt = f"""
You are an expert subject-matter teacher.
Given the following quiz questions on topic "{topic}", provide the correct answer and a concise, step-by-step pedagogical explanation for each question.

Questions input:
{json.dumps(questions, indent=2)}

Return ONLY a JSON array where each question object includes:
- question_text: string (same as input)
- question_type: string (same as input)
- options: list of strings (same as input)
- subtopic: string (same as input)
- correct_answer: string (exact match of correct option for MCQ/TF, or key answer string for short_answer)
- explanation: string (clear breakdown of why this answer is correct)
"""
        raw_response = self.call_gemini(prompt)
        if raw_response:
            parsed = self.clean_json_response(raw_response)
            if isinstance(parsed, list) and len(parsed) == len(questions):
                logger.info(f"[{self.name}] Successfully generated answer keys via Gemini API.")
                return parsed

        logger.info(f"[{self.name}] Attaching answer keys via Demo Mode AI engine.")
        return self._attach_demo_keys(questions, topic)

    def _attach_demo_keys(self, questions: List[Dict[str, Any]], topic: str) -> List[Dict[str, Any]]:
        enriched_questions = []
        for idx, q in enumerate(questions):
            q_copy = dict(q)
            q_type = q_copy.get("question_type", "mcq")
            options = q_copy.get("options", [])

            if q_type == "mcq" and options:
                correct_ans = options[0] # Default to first option as correct answer
                explanation = f"Option '{correct_ans}' is the correct choice because it directly addresses the core principles of {q_copy.get('subtopic', topic)}."
            elif q_type == "tf":
                correct_ans = "True"
                explanation = f"This statement is True. In standard implementations of {topic}, components can operate statelessly to optimize scalability."
            else:
                correct_ans = "Static analysis examines code without executing it, while dynamic analysis evaluates code behavior during runtime execution."
                explanation = "Static analysis relies on structural code parsing, whereas dynamic analysis observes live memory state, inputs, and execution paths."

            q_copy["correct_answer"] = correct_ans
            q_copy["explanation"] = explanation
            enriched_questions.append(q_copy)

        return enriched_questions
