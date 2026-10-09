import json
import logging
from typing import List, Dict, Any
from agents.base_agent import BaseAgent

logger = logging.getLogger("WeakAreaAnalyzerAgent")

class WeakAreaAnalyzerAgent(BaseAgent):
    """
    Agent #6: Analyzes student responses by subtopic, identifies weak areas,
    and formulates personalized remedial recommendations.
    """
    def __init__(self):
        super().__init__(
            name="Weak Area Analyzer Agent",
            role_description="Aggregates topic performance, detects knowledge gaps, and recommends targeted study topics."
        )

    def analyze_performance(
        self, topic: str, score_percentage: float, breakdown: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Groups results by subtopic and performs gap analysis.
        """
        subtopic_stats = {}
        for item in breakdown:
            sub = item.get("subtopic", "General Core")
            if sub not in subtopic_stats:
                subtopic_stats[sub] = {"total": 0, "correct": 0}
            subtopic_stats[sub]["total"] += 1
            if item.get("is_correct") == 1 or item.get("points_awarded", 0) >= 0.7:
                subtopic_stats[sub]["correct"] += 1

        weak_topics = []
        strengths = []

        for sub, stats in subtopic_stats.items():
            acc = (stats["correct"] / stats["total"]) * 100
            if acc < 70.0:
                weak_topics.append({"subtopic": sub, "accuracy": round(acc, 1)})
            else:
                strengths.append({"subtopic": sub, "accuracy": round(acc, 1)})

        prompt = f"""
You are an expert academic advisor AI.
A student took a quiz on "{topic}" and scored {score_percentage}%.
Subtopic Analysis:
Weak Subtopics: {json.dumps(weak_topics)}
Strong Subtopics: {json.dumps(strengths)}

Provide 3 actionable, specific remedial recommendations for the student to improve.
Return ONLY JSON:
{{
  "recommendations": [
    "Recommendation 1...",
    "Recommendation 2...",
    "Recommendation 3..."
  ]
}}
"""
        raw_response = self.call_gemini(prompt)
        recommendations = []
        if raw_response:
            parsed = self.clean_json_response(raw_response)
            if "recommendations" in parsed and isinstance(parsed["recommendations"], list):
                recommendations = parsed["recommendations"]

        if not recommendations:
            recommendations = self._generate_demo_recommendations(topic, weak_topics)

        return {
            "weak_topics": weak_topics if weak_topics else [{"subtopic": f"General {topic} Synthesis", "accuracy": score_percentage}],
            "strengths": strengths if strengths else [{"subtopic": f"Basic {topic} Terminology", "accuracy": score_percentage}],
            "recommendations": recommendations,
            "status": "generated" # requires faculty approval
        }

    def _generate_demo_recommendations(self, topic: str, weak_topics: List[Dict[str, Any]]) -> List[str]:
        if not weak_topics:
            return [
                f"Great work! Maintain mastery in {topic} by attempting advanced problem sets.",
                "Explore real-world case studies and application scenarios.",
                "Assist peers to consolidate your top-tier understanding."
            ]

        recs = []
        for w in weak_topics[:2]:
            sub = w.get("subtopic", topic)
            recs.append(f"Review core principles and practical examples for subtopic: '{sub}'.")

        recs.append(f"Re-attempt practice questions focusing specifically on concept application in {topic}.")
        return recs
