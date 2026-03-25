import re
from typing import List, Dict


class SimpleReranker:
    @staticmethod
    def _tokenize(text: str) -> set[str]:
        tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        return set(tokens)

    @classmethod
    def rerank(cls, question: str, results: List[Dict], top_n: int = 5) -> List[Dict]:
        q_tokens = cls._tokenize(question)

        reranked = []
        for item in results:
            chunk_text = item.get("chunk_text", "")
            section_title = (item.get("section_title") or "").lower()

            chunk_tokens = cls._tokenize(chunk_text)
            overlap = len(q_tokens.intersection(chunk_tokens))

            section_bonus = 0.0
            if "risk factors" in section_title and ("risk" in question.lower() or "competition" in question.lower()):
                section_bonus += 0.08
            if "management" in section_title and ("financial" in question.lower() or "results" in question.lower()):
                section_bonus += 0.05

            base_similarity = float(item.get("similarity", 0.0))
            final_score = base_similarity + (0.01 * overlap) + section_bonus

            new_item = dict(item)
            new_item["rerank_score"] = round(final_score, 6)
            reranked.append(new_item)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_n]