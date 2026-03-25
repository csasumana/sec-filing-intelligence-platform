from typing import List, Dict


class CitationBuilder:
    @staticmethod
    def build_citations(results: List[Dict]) -> List[Dict]:
        citations = []

        for idx, item in enumerate(results, start=1):
            citations.append({
                "citation_id": idx,
                "filing_id": item.get("filing_id"),
                "section_title": item.get("section_title"),
                "chunk_index": item.get("chunk_index"),
            })

        return citations

    @staticmethod
    def format_context(results: List[Dict]) -> str:
        context_parts = []

        for idx, item in enumerate(results, start=1):
            section_title = item.get("section_title", "Unknown Section")
            chunk_index = item.get("chunk_index", "NA")
            chunk_text = item.get("chunk_text", "")

            context_parts.append(
                f"[CITATION {idx}] "
                f"Section: {section_title} | Chunk: {chunk_index}\n"
                f"{chunk_text}"
            )

        return "\n\n".join(context_parts)