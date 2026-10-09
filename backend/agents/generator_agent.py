import json
import logging
from typing import List, Dict, Any
from agents.base_agent import BaseAgent

logger = logging.getLogger("QuizGeneratorAgent")

class QuizGeneratorAgent(BaseAgent):
    """
    Agent #1: Responsible for crafting raw quiz questions (stems, options, subtopics, question types).
    """
    def __init__(self):
        super().__init__(
            name="Quiz Generator Agent",
            role_description="Specializes in generating high-quality pedagogical question stems, distractors, and subtopic mappings."
        )

    def generate_questions(self, topic: str, difficulty: str, count: int, question_types: List[str]) -> List[Dict[str, Any]]:
        prompt = f"""
You are an expert educational assessment creator.
Generate {count} quiz questions on the topic: "{topic}".
Target Difficulty Level: {difficulty}
Allowed Question Types: {', '.join(question_types)}

Return ONLY a valid JSON array of objects with the following keys:
- question_text: string (clear question prompt)
- question_type: string ("mcq", "tf", or "short_answer")
- options: list of strings (for MCQ specify 4 choices; for TF specify ["True", "False"]; for short_answer specify empty list [])
- subtopic: string (the specific concept or sub-domain being tested)

Do not include any explanation or extra text outside the JSON array.
"""
        raw_response = self.call_gemini(prompt)
        if raw_response:
            parsed = self.clean_json_response(raw_response)
            if isinstance(parsed, list) and len(parsed) > 0:
                logger.info(f"[{self.name}] Successfully generated {len(parsed)} questions via Gemini API.")
                return parsed

        logger.info(f"[{self.name}] Generating {count} questions via Demo Mode AI engine for '{topic}'.")
        return self._generate_demo_questions(topic, difficulty, count, question_types)

    def _generate_demo_questions(self, topic: str, difficulty: str, count: int, question_types: List[str]) -> List[Dict[str, Any]]:
        questions = []
        types_to_use = question_types if question_types else ["mcq", "tf", "short_answer"]
        
        # Smart template database for demo mode
        topic_lower = topic.lower()
        
        for i in range(1, count + 1):
            q_type = types_to_use[(i - 1) % len(types_to_use)]
            
            if q_type == "mcq":
                if "python" in topic_lower or "programming" in topic_lower or "code" in topic_lower:
                    item = {
                        "question_text": f"Q{i}: What is the primary purpose of the '{'def' if i%2==1 else 'return'}' keyword in Python?",
                        "question_type": "mcq",
                        "options": [
                            "To define a new function in Python",
                            "To import an external library module",
                            "To terminate loop execution immediately",
                            "To declare a global variable"
                        ] if i%2==1 else [
                            "To send a value back from a function to its caller",
                            "To print text directly to the console",
                            "To handle runtime exceptions",
                            "To instantiate a new class object"
                        ],
                        "subtopic": "Functions & Syntax" if i%2==1 else "Control Flow & Return Values"
                    }
                elif "data" in topic_lower or "db" in topic_lower or "sql" in topic_lower:
                    item = {
                        "question_text": f"Q{i}: Which SQL clause is used to filter records after aggregation in SQL?",
                        "question_type": "mcq",
                        "options": ["HAVING", "WHERE", "GROUP BY", "ORDER BY"],
                        "subtopic": "SQL Queries & Aggregations"
                    }
                else:
                    item = {
                        "question_text": f"Q{i}: Which key fundamental concept best explains the core principle of {topic} (Concept {i})?",
                        "question_type": "mcq",
                        "options": [
                            f"Primary core mechanism of {topic}",
                            f"Secondary auxiliary process of {topic}",
                            f"Deprecated legacy standard of {topic}",
                            f"Unrelated outer framework component"
                        ],
                        "subtopic": f"{topic} Foundations - Part {i}"
                    }
            elif q_type == "tf":
                item = {
                    "question_text": f"Q{i}: Is it True or False that in {topic}, key architectural components can operate statelessly?",
                    "question_type": "tf",
                    "options": ["True", "False"],
                    "subtopic": f"{topic} Architecture"
                }
            else: # short_answer
                item = {
                    "question_text": f"Q{i}: Briefly explain the main difference between static and dynamic analysis in {topic}.",
                    "question_type": "short_answer",
                    "options": [],
                    "subtopic": f"{topic} Analysis Techniques"
                }
                
            questions.append(item)
            
        return questions
