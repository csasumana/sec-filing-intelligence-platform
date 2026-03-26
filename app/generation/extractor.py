import json
from google import genai

from app.core.config import settings


class Extractor:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract_field(self, field_name: str, question: str, context: str) -> dict:
        prompt = f"""
You are a financial filing extraction assistant.

Extract the requested field ONLY from the provided evidence.
Do NOT use outside knowledge.

Return STRICT JSON only with this exact schema:
{{
  "field": "{field_name}",
  "value": "string or null",
  "status": "found" or "not_found",
  "reasoning": "very short explanation"
}}

Rules:
1. If the evidence is insufficient, set:
   - "value": null
   - "status": "not_found"
2. Keep the value concise.
3. Do not include markdown fences.
4. Return valid JSON only.

Field request:
{question}

Evidence:
{context}
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw = (response.text or "").strip()

        try:
            return json.loads(raw)
        except Exception:
            # Fallback if model returns imperfect JSON
            return {
                "field": field_name,
                "value": None,
                "status": "not_found",
                "reasoning": f"Failed to parse model output: {raw[:200]}"
            }