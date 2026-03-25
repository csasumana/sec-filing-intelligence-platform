from typing import List


class Chunker:
    @staticmethod
    def chunk_text(text: str, max_chars: int = 1800, overlap: int = 250) -> List[str]:
        """
        Simple character-based chunking for Day 2.
        Later we'll make this token-aware and smarter.
        """
        if not text or len(text.strip()) == 0:
            return []

        text = text.strip()

        if len(text) <= max_chars:
            return [text]

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + max_chars, text_length)
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end == text_length:
                break

            start = max(0, end - overlap)

        return chunks