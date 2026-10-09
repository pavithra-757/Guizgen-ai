import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("QuizGenAgents")
logging.basicConfig(level=logging.INFO)

class BaseAgent:
    """
    Base Agent that handles integration with Google Gemini API
    and fallback to smart deterministic demo generation if API key is missing/invalid.
    """
    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.using_demo_mode = False if (self.api_key and self.api_key != "your_gemini_api_key_here") else True

    def call_gemini(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Attempts to call Google Gemini API. Returns raw response string or None if unconfigured/failed.
        """
        if self.using_demo_mode:
            logger.info(f"[{self.name}] Operating in Demo Mode (GEMINI_API_KEY missing or placeholder).")
            return None

        try:
            # Try google-genai SDK first if available
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config={'system_instruction': system_instruction} if system_instruction else None
                )
                if response and hasattr(response, 'text'):
                    return response.text
            except ImportError:
                # Fallback to google-generativeai package
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                if response and hasattr(response, 'text'):
                    return response.text

        except Exception as e:
            logger.warning(f"[{self.name}] Gemini API call failed: {e}. Falling back to agent internal logic.")
            return None

        return None

    def clean_json_response(self, text: str) -> Dict[str, Any]:
        """
        Utility to extract and parse JSON from Markdown code fences or raw text.
        """
        if not text:
            return {}
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        try:
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"[{self.name}] JSON parsing error: {e}")
            return {}
