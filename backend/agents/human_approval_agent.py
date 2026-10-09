import logging
from typing import Dict, Any, List

logger = logging.getLogger("HumanApprovalAgent")

class HumanApprovalAgent:
    """
    Agent #4: Enforces Human-in-the-Loop review rules, validates manual edits,
    and guards the publishing gate.
    """
    def __init__(self):
        self.name = "Human Approval Agent"

    def can_publish_quiz(self, quiz_status: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates whether a quiz meets all Human-in-the-Loop requirements for publication.
        Must be approved by faculty, and all individual questions must be approved or resolved.
        """
        if quiz_status != "approved":
            return {
                "allowed": False,
                "reason": f"Quiz status is currently '{quiz_status}'. A faculty member must explicitly approve the entire quiz before publishing."
            }

        unapproved_questions = [
            q for q in questions if q.get("status") in ["flagged", "pending", "rejected"]
        ]
        
        if unapproved_questions:
            return {
                "allowed": False,
                "reason": f"There are {len(unapproved_questions)} unapproved/flagged question(s). Please review and approve all individual items."
            }

        return {
            "allowed": True,
            "reason": "All human-in-the-loop validation criteria satisfied. Quiz is ready for publication."
        }

    def process_question_edit(self, original: Dict[str, Any], edited_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies faculty edits to a question and upgrades its quality status to 'edited' or 'approved'.
        """
        updated = dict(original)
        
        if "question_text" in edited_data:
            updated["question_text"] = edited_data["question_text"]
        if "options" in edited_data:
            updated["options"] = edited_data["options"]
        if "correct_answer" in edited_data:
            updated["correct_answer"] = edited_data["correct_answer"]
        if "explanation" in edited_data:
            updated["explanation"] = edited_data["explanation"]
        if "subtopic" in edited_data:
            updated["subtopic"] = edited_data["subtopic"]

        # Human override elevates quality score and marks as edited/approved
        updated["quality_score"] = 1.0
        updated["status"] = "edited"
        updated["feedback_notes"] = "Faculty manually edited and verified this question."

        logger.info(f"[{self.name}] Applied faculty edits to question ID: {original.get('id')}")
        return updated
