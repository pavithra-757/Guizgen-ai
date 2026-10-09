import logging
from typing import List, Dict, Any, Optional

from agents.generator_agent import QuizGeneratorAgent
from agents.answer_key_agent import AnswerKeyAgent
from agents.quality_checker_agent import QualityCheckerAgent
from agents.human_approval_agent import HumanApprovalAgent
from agents.evaluator_agent import EvaluationAgent
from agents.weak_area_analyzer_agent import WeakAreaAnalyzerAgent

logger = logging.getLogger("CentralAgentOrchestrator")

class CentralAgentOrchestrator:
    """
    Agent #7: Orchestrates end-to-end multi-agent pipelines for quiz generation,
    quality control, evaluation, and weak area analysis.
    """
    def __init__(self):
        self.generator = QuizGeneratorAgent()
        self.answer_key_agent = AnswerKeyAgent()
        self.quality_checker = QualityCheckerAgent()
        self.human_approval = HumanApprovalAgent()
        self.evaluator = EvaluationAgent()
        self.weak_area_analyzer = WeakAreaAnalyzerAgent()

    def run_quiz_generation_pipeline(
        self, topic: str, difficulty: str, count: int, question_types: List[str]
    ) -> Dict[str, Any]:
        """
        Runs Step 1 -> Step 2 -> Step 3 multi-agent generation pipeline.
        1. Generator Agent -> Raw questions
        2. Answer Key Agent -> Correct answers & explanations
        3. Quality Checker Agent -> Quality scoring & audit flags
        """
        logger.info(f"[Orchestrator] Starting Quiz Generation Pipeline for topic: '{topic}'")
        
        # Step 1: Raw question generation
        raw_questions = self.generator.generate_questions(topic, difficulty, count, question_types)
        
        # Step 2: Answer key & explanation attachment
        questions_with_keys = self.answer_key_agent.attach_answer_keys(raw_questions, topic)
        
        # Step 3: Quality audit & scoring
        audited_questions = self.quality_checker.audit_questions(questions_with_keys, difficulty)

        flagged_count = sum(1 for q in audited_questions if q.get("status") == "flagged")

        logger.info(f"[Orchestrator] Generation Pipeline complete. {len(audited_questions)} questions generated ({flagged_count} flagged for human review).")
        
        return {
            "topic": topic,
            "difficulty": difficulty,
            "questions": audited_questions,
            "flagged_count": flagged_count,
            "pipeline_status": "pending_faculty_approval"
        }

    def run_student_evaluation_pipeline(
        self, topic: str, questions: List[Dict[str, Any]], student_answers: Dict[int, str]
    ) -> Dict[str, Any]:
        """
        Runs evaluation -> weak area analysis multi-agent pipeline.
        1. Evaluation Agent -> Grade submission
        2. Weak Area Analyzer Agent -> Analyze gaps & study plan
        """
        logger.info(f"[Orchestrator] Starting Student Evaluation Pipeline.")
        
        # Step 1: Auto-grade submission
        eval_results = self.evaluator.evaluate_submission(questions, student_answers)
        
        # Step 2: Perform weak area analysis
        report = self.weak_area_analyzer.analyze_performance(
            topic=topic,
            score_percentage=eval_results["percentage"],
            breakdown=eval_results["breakdown"]
        )

        return {
            "score": eval_results["score"],
            "max_score": eval_results["max_score"],
            "percentage": eval_results["percentage"],
            "breakdown": eval_results["breakdown"],
            "report": report
        }

    def validate_publishing(self, quiz_status: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Delegates publishing authorization check to Human Approval Agent.
        """
        return self.human_approval.can_publish_quiz(quiz_status, questions)
