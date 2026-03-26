import json
from google import genai

from app.core.config import settings


class Comparator:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def compare_filings(self, focus: str, base_context: str, compare_context: str) -> dict:
        prompt = f"""
You are a financial filings comparison assistant.

Compare two SEC filing evidence sets for the focus area: {focus}

Return STRICT JSON only with this exact schema:
{{
  "focus": "{focus}",
  "summary": "2-5 sentence comparison summary",
  "new_or_more_emphasized_in_compare": ["bullet 1", "bullet 2"],
  "materially_similar_points": ["bullet 1", "bullet 2"]
}}

Rules:
1. Use ONLY the provided evidence.
2. Do NOT use outside knowledge.
3. If evidence is weak, still make a cautious comparison based only on the evidence.
4. Keep bullets concise.
5. Return valid JSON only. No markdown fences.

BASE FILING EVIDENCE:
{base_context}

COMPARE FILING EVIDENCE:
{compare_context}
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw = (response.text or "").strip()

        try:
            return json.loads(raw)
        except Exception:
            return {
                "focus": focus,
                "summary": "Comparison failed due to JSON parsing issue.",
                "new_or_more_emphasized_in_compare": [],
                "materially_similar_points": [],
                "raw_model_output": raw[:500]
            }