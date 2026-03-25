from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.services.ingest_service import IngestService
from app.indexing.embedder import Embedder
from app.indexing.vector_store import VectorStore
from app.retrieval.reranker import SimpleReranker
from app.retrieval.citation_builder import CitationBuilder
from app.generation.answer_generator import AnswerGenerator


app = FastAPI(title=settings.APP_NAME)

ingest_service = IngestService()
embedder = Embedder()
vector_store = VectorStore()
answer_generator = AnswerGenerator()


class IngestRequest(BaseModel):
    filing_url: str
    output_filename: str


class RetrieveRequest(BaseModel):
    question: str
    filing_id: str | None = None
    top_k: int = 5


class QueryRequest(BaseModel):
    question: str
    filing_id: str | None = None
    top_k: int = 5


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.post("/filings/ingest")
def ingest_filing(payload: IngestRequest):
    try:
        result = ingest_service.ingest_from_url(
            filing_url=payload.filing_url,
            output_filename=payload.output_filename
        )

        return {
            "filing_id": result["metadata"]["filing_id"],
            "company_name": result["metadata"]["company_name"],
            "ticker": result["metadata"]["ticker"],
            "form_type": result["metadata"]["form_type"],
            "section_count": len(result["sections"]),
            "total_chunks": result["total_chunks"],
            "local_path": result["local_path"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retrieve/debug")
def retrieve_debug(payload: RetrieveRequest):
    try:
        query_embedding = embedder.embed_text(payload.question)
        results = vector_store.search_similar_chunks(
            query_embedding=query_embedding,
            filing_id=payload.filing_id,
            top_k=payload.top_k,
        )

        return {
            "question": payload.question,
            "filing_id_filter": payload.filing_id,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
def query_filing(payload: QueryRequest):
    try:
        # Step 1: retrieve more candidates
        query_embedding = embedder.embed_text(payload.question)
        candidates = vector_store.search_similar_chunks_for_rag(
            query_embedding=query_embedding,
            filing_id=payload.filing_id,
            candidate_k=max(10, payload.top_k * 2),
        )

        if not candidates:
            return {
                "answer": "INSUFFICIENT_EVIDENCE",
                "insufficient_evidence": True,
                "citations": [],
                "evidence": []
            }

        # Step 2: rerank
        top_results = SimpleReranker.rerank(
            question=payload.question,
            results=candidates,
            top_n=payload.top_k,
        )

        # Step 3: lightweight insufficient evidence guard
        best_score = float(top_results[0].get("rerank_score", 0.0)) if top_results else 0.0
        if best_score < 0.45:
            return {
                "answer": "INSUFFICIENT_EVIDENCE",
                "insufficient_evidence": True,
                "citations": [],
                "evidence": top_results
            }

        # Step 4: build context + citations
        context = CitationBuilder.format_context(top_results)
        citations = CitationBuilder.build_citations(top_results)

        # Step 5: generate grounded answer
        answer = answer_generator.generate_grounded_answer(
            question=payload.question,
            context=context
        )

        insufficient = answer.strip() == "INSUFFICIENT_EVIDENCE"

        return {
            "answer": answer,
            "insufficient_evidence": insufficient,
            "citations": citations,
            "evidence": top_results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))