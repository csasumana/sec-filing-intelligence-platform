import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from app.ingestion.filing_parser import FilingParser
from app.ingestion.section_splitter import SectionSplitter
from app.ingestion.sec_fetcher import SECFetcher
from app.indexing.chunker import Chunker
from app.indexing.embedder import Embedder
from app.indexing.vector_store import VectorStore


class IngestService:
    def __init__(self):
        self.fetcher = SECFetcher()
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    def _extract_metadata(self, raw_text: str, filing_url: str) -> Dict:
        company_name = None
        ticker = None
        cik = None
        form_type = None
        filing_date = None
        accession_number = None

        # CIK from SEC URL
        cik_match = re.search(r"/data/(\d+)/", filing_url)
        if cik_match:
            cik = cik_match.group(1).lstrip("0") or cik_match.group(1)

        # Accession from SEC URL
        accession_match = re.search(r"/data/\d+/(\d+)/", filing_url)
        if accession_match:
            accession_number = accession_match.group(1)

        # Basic form type detection
        if "10-K" in raw_text[:5000]:
            form_type = "10-K"
        elif "10-Q" in raw_text[:5000]:
            form_type = "10-Q"

        # Try to extract filing date from filename pattern like aapl-20250927
        file_match = re.search(r"([a-z]+)-(\d{8})", raw_text[:200])
        if file_match:
            date_str = file_match.group(2)
            try:
                filing_date = datetime.strptime(date_str, "%Y%m%d").date()
            except ValueError:
                pass

        # Try to infer company from known text
        if "Apple Inc." in raw_text[:3000]:
            company_name = "Apple Inc."
            ticker = "AAPL"

        filing_id = f"{ticker or 'unknown'}_{form_type or 'unknown'}_{accession_number or 'na'}"

        return {
            "filing_id": filing_id,
            "company_name": company_name,
            "ticker": ticker,
            "cik": cik,
            "form_type": form_type,
            "filing_date": filing_date,
            "accession_number": accession_number,
        }

    def ingest_from_url(self, filing_url: str, output_filename: str) -> Dict:
        local_path = self.fetcher.download_filing_html(filing_url, output_filename)

        html_content = Path(local_path).read_text(encoding="utf-8")
        raw_text = FilingParser.html_to_text(html_content)
        sections = SectionSplitter.split_sections(raw_text)

        metadata = self._extract_metadata(raw_text, filing_url)

        # Save filing
        self.vector_store.insert_filing(
            filing_id=metadata["filing_id"],
            company_name=metadata["company_name"],
            ticker=metadata["ticker"],
            cik=metadata["cik"],
            form_type=metadata["form_type"],
            filing_date=metadata["filing_date"],
            accession_number=metadata["accession_number"],
            source_url=filing_url,
            local_path=str(local_path),
            raw_text=raw_text,
        )

        total_chunks = 0

        for section in sections:
            section_id = self.vector_store.insert_section(
                filing_id=metadata["filing_id"],
                section_label=section["section_label"],
                section_title=section["section_title"],
                section_text=section["section_text"],
                section_order=section["section_order"],
            )

            chunks = Chunker.chunk_text(section["section_text"])

            if not chunks:
                continue

            embeddings = self.embedder.embed_texts(chunks)

            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings), start=1):
                token_estimate = max(1, len(chunk_text) // 4)

                self.vector_store.insert_chunk(
                    filing_id=metadata["filing_id"],
                    section_id=section_id,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    token_estimate=token_estimate,
                    embedding=embedding,
                )
                total_chunks += 1

        return {
            "local_path": str(local_path),
            "raw_text": raw_text,
            "sections": sections,
            "metadata": metadata,
            "total_chunks": total_chunks,
        }