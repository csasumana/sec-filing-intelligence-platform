from datetime import date
from typing import Optional, List

from sqlalchemy import text

from app.core.database import SessionLocal


class VectorStore:
    def delete_filing_data(self, filing_id: str):
        with SessionLocal() as session:
            session.execute(
                text("DELETE FROM filing_chunks WHERE filing_id = :filing_id"),
                {"filing_id": filing_id}
            )
            session.execute(
                text("DELETE FROM filing_sections WHERE filing_id = :filing_id"),
                {"filing_id": filing_id}
            )
            session.execute(
                text("DELETE FROM filings WHERE filing_id = :filing_id"),
                {"filing_id": filing_id}
            )
            session.commit()

    def insert_filing(
        self,
        filing_id: str,
        company_name: Optional[str],
        ticker: Optional[str],
        cik: Optional[str],
        form_type: Optional[str],
        filing_date: Optional[date],
        accession_number: Optional[str],
        source_url: str,
        local_path: str,
        raw_text: str,
    ):
        with SessionLocal() as session:
            session.execute(
                text("""
                    INSERT INTO filings (
                        filing_id, company_name, ticker, cik, form_type,
                        filing_date, accession_number, source_url, local_path, raw_text
                    )
                    VALUES (
                        :filing_id, :company_name, :ticker, :cik, :form_type,
                        :filing_date, :accession_number, :source_url, :local_path, :raw_text
                    )
                """),
                {
                    "filing_id": filing_id,
                    "company_name": company_name,
                    "ticker": ticker,
                    "cik": cik,
                    "form_type": form_type,
                    "filing_date": filing_date,
                    "accession_number": accession_number,
                    "source_url": source_url,
                    "local_path": local_path,
                    "raw_text": raw_text,
                }
            )
            session.commit()

    def insert_section(
        self,
        filing_id: str,
        section_label: str,
        section_title: str,
        section_text: str,
        section_order: int,
    ) -> int:
        with SessionLocal() as session:
            result = session.execute(
                text("""
                    INSERT INTO filing_sections (
                        filing_id, section_label, section_title, section_text, section_order
                    )
                    VALUES (
                        :filing_id, :section_label, :section_title, :section_text, :section_order
                    )
                    RETURNING id
                """),
                {
                    "filing_id": filing_id,
                    "section_label": section_label,
                    "section_title": section_title,
                    "section_text": section_text,
                    "section_order": section_order,
                }
            )
            section_id = result.scalar()
            session.commit()
            return section_id

    def insert_chunk(
        self,
        filing_id: str,
        section_id: int,
        chunk_index: int,
        chunk_text: str,
        token_estimate: int,
        embedding: List[float],
    ):
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        with SessionLocal() as session:
            session.execute(
                text("""
                    INSERT INTO filing_chunks (
                        filing_id, section_id, chunk_index, chunk_text, token_estimate, embedding
                    )
                    VALUES (
                        :filing_id, :section_id, :chunk_index, :chunk_text, :token_estimate, CAST(:embedding AS vector)
                    )
                """),
                {
                    "filing_id": filing_id,
                    "section_id": section_id,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text,
                    "token_estimate": token_estimate,
                    "embedding": embedding_str,
                }
            )
            session.commit()

    def search_similar_chunks(
        self,
        query_embedding: List[float],
        filing_id: Optional[str] = None,
        top_k: int = 5,
    ):
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        base_sql = """
            SELECT
                fc.id,
                fc.filing_id,
                fs.section_title,
                fc.chunk_index,
                fc.chunk_text,
                fc.token_estimate,
                1 - (fc.embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM filing_chunks fc
            JOIN filing_sections fs ON fc.section_id = fs.id
        """

        where_clause = ""
        params = {
            "embedding": embedding_str,
            "top_k": top_k,
        }

        if filing_id:
            where_clause = " WHERE fc.filing_id = :filing_id "
            params["filing_id"] = filing_id

        order_clause = """
            ORDER BY fc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """

        sql = text(base_sql + where_clause + order_clause)

        with SessionLocal() as session:
            result = session.execute(sql, params)
            rows = result.mappings().all()
            return [dict(row) for row in rows]

    def search_similar_chunks_for_rag(
        self,
        query_embedding: List[float],
        filing_id: Optional[str] = None,
        candidate_k: int = 12,
    ):
        return self.search_similar_chunks(
            query_embedding=query_embedding,
            filing_id=filing_id,
            top_k=candidate_k,
        )