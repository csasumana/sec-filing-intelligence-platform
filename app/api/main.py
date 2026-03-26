from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.prompts import EXTRACTION_FIELD_QUERIES, COMPARE_FOCUS_QUERIES
from app.services.ingest_service import IngestService
from app.indexing.embedder import Embedder
from app.indexing.vector_store import VectorStore
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.citation_builder import CitationBuilder
from app.generation.answer_generator import AnswerGenerator
from app.generation.extractor import Extractor
from app.generation.comparator import Comparator


app = FastAPI(title=settings.APP_NAME)

ingest_service = IngestService()
embedder = Embedder()
vector_store = VectorStore()
answer_generator = AnswerGenerator()
extractor = Extractor()
comparator = Comparator()


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


class ExtractRequest(BaseModel):
    filing_id: str
    fields: list[str]


class CompareRequest(BaseModel):
    base_filing_id: str
    compare_filing_id: str
    focus: str
    top_k: int = 4


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

        top_results = CrossEncoderReranker.rerank(
            question=payload.question,
            results=candidates,
            top_n=payload.top_k,
        )

        best_score = float(top_results[0].get("rerank_score", 0.0)) if top_results else 0.0
        if best_score < 0.45:
            return {
                "answer": "INSUFFICIENT_EVIDENCE",
                "insufficient_evidence": True,
                "citations": [],
                "evidence": top_results
            }

        context = CitationBuilder.format_context(top_results)
        citations = CitationBuilder.build_citations(top_results)

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


@app.post("/extract")
def extract_fields(payload: ExtractRequest):
    try:
        output = []

        for field in payload.fields:
            if field not in EXTRACTION_FIELD_QUERIES:
                output.append({
                    "field": field,
                    "value": None,
                    "status": "not_found",
                    "reasoning": "Unsupported field",
                    "citations": []
                })
                continue

            question = EXTRACTION_FIELD_QUERIES[field]

            query_embedding = embedder.embed_text(question)
            candidates = vector_store.search_similar_chunks_for_rag(
                query_embedding=query_embedding,
                filing_id=payload.filing_id,
                candidate_k=10,
            )

            if not candidates:
                output.append({
                    "field": field,
                    "value": None,
                    "status": "not_found",
                    "reasoning": "No evidence retrieved",
                    "citations": []
                })
                continue

            top_results = CrossEncoderReranker.rerank(
                question=question,
                results=candidates,
                top_n=4,
            )

            context = CitationBuilder.format_context(top_results)
            citations = CitationBuilder.build_citations(top_results)

            extracted = extractor.extract_field(
                field_name=field,
                question=question,
                context=context
            )

            extracted["citations"] = citations
            extracted["evidence"] = top_results
            output.append(extracted)

        return {
            "filing_id": payload.filing_id,
            "results": output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare")
def compare_filings(payload: CompareRequest):
    try:
        if payload.focus not in COMPARE_FOCUS_QUERIES:
            raise HTTPException(status_code=400, detail=f"Unsupported focus: {payload.focus}")

        question = COMPARE_FOCUS_QUERIES[payload.focus]
        query_embedding = embedder.embed_text(question)

        base_candidates = vector_store.search_similar_chunks_for_rag(
            query_embedding=query_embedding,
            filing_id=payload.base_filing_id,
            candidate_k=max(8, payload.top_k * 2),
        )
        compare_candidates = vector_store.search_similar_chunks_for_rag(
            query_embedding=query_embedding,
            filing_id=payload.compare_filing_id,
            candidate_k=max(8, payload.top_k * 2),
        )

        if not base_candidates or not compare_candidates:
            return {
                "focus": payload.focus,
                "comparison": None,
                "base_evidence": [],
                "compare_evidence": [],
                "error": "Insufficient evidence from one or both filings"
            }

        base_top = CrossEncoderReranker.rerank(
            question=question,
            results=base_candidates,
            top_n=payload.top_k,
        )
        compare_top = CrossEncoderReranker.rerank(
            question=question,
            results=compare_candidates,
            top_n=payload.top_k,
        )

        base_context = CitationBuilder.format_context(base_top)
        compare_context = CitationBuilder.format_context(compare_top)

        comparison = comparator.compare_filings(
            focus=payload.focus,
            base_context=base_context,
            compare_context=compare_context
        )

        return {
            "focus": payload.focus,
            "base_filing_id": payload.base_filing_id,
            "compare_filing_id": payload.compare_filing_id,
            "comparison": comparison,
            "base_citations": CitationBuilder.build_citations(base_top),
            "compare_citations": CitationBuilder.build_citations(compare_top),
            "base_evidence": base_top,
            "compare_evidence": compare_top,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))