from google import genai

from app.core.config import settings


class AnswerGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_grounded_answer(self, question: str, context: str) -> str:
        prompt = f"""
You are a financial filing analysis assistant.

Answer the user's question ONLY using the provided evidence chunks.
Do NOT use outside knowledge.
If the evidence is insufficient, say exactly:
INSUFFICIENT_EVIDENCE

Rules:
1. Be concise but specific.
2. Use only facts supported by the evidence.
3. If multiple evidence chunks support the answer, synthesize them.
4. When making factual claims, include inline citation IDs like [1], [2].
5. Do not invent company facts not present in the evidence.

User question:
{question}

Evidence:
{context}

Return only the final answer text.
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return (response.text or "").strip()