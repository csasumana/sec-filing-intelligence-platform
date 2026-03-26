from typing import List, Dict
from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            cls._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return cls._model

    @classmethod
    def rerank(cls, question: str, results: List[Dict], top_n: int = 5) -> List[Dict]:
        if not results:
            return []

        model = cls._get_model()

        pairs = []
        for item in results:
            chunk_text = item.get("chunk_text", "")
            section_title = item.get("section_title", "")
            combined_text = f"Section: {section_title}\n{chunk_text}"
            pairs.append((question, combined_text))

        scores = model.predict(pairs)

        reranked = []
        for item, score in zip(results, scores):
            new_item = dict(item)
            new_item["rerank_score"] = float(score)
            reranked.append(new_item)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_n]