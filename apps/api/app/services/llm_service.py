from typing import Dict, Any, Optional
from app.core.config import settings
import json


class LLMService:
    def __init__(self):
        self.enabled = bool(settings.GEMINI_API_KEY)
        self.model_name = settings.LLM_MODEL

    async def extract_structured(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt + "\n\nRespond ONLY with valid JSON.")
            text = response.text
            # Try to extract JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            return json.loads(text)
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return None

    async def explain_match(self, profile_facts: list, scheme: Dict[str, Any], condition_results: list) -> str:
        if not self.enabled:
            return "Match evaluated using deterministic rules against published conditions. See condition-by-condition breakdown below."
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(self.model_name)
            prompt = f"""Explain this scheme match in plain language for an Indian citizen.
Be factual, cite official source, never guarantee eligibility/approval.
Profile facts: {json.dumps(profile_facts)}
Scheme: {scheme.get('name')} - {scheme.get('official_source_url')}
Condition results: {json.dumps(condition_results)}

Provide a clear explanation."""
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            return "Match evaluated using deterministic rules. Always verify with the official source before applying."


llm_service = LLMService()
