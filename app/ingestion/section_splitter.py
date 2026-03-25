import re
from typing import List, Dict


class SectionSplitter:
    SECTION_PATTERNS = [
        r"(Item\s+1A\.?\s+Risk\s+Factors)",
        r"(Item\s+1\.?\s+Business)",
        r"(Item\s+3\.?\s+Legal\s+Proceedings)",
        r"(Item\s+7\.?\s+Management['’]s\s+Discussion\s+and\s+Analysis)",
        r"(Item\s+7A\.?\s+Quantitative\s+and\s+Qualitative\s+Disclosures\s+About\s+Market\s+Risk)",
        r"(Item\s+8\.?\s+Financial\s+Statements)",
        r"(Part\s+I,\s*Item\s+2\.?\s+Management['’]s\s+Discussion\s+and\s+Analysis)",
        r"(Part\s+II,\s*Item\s+1A\.?\s+Risk\s+Factors)",
    ]

    @classmethod
    def split_sections(cls, text: str) -> List[Dict]:
        pattern = "|".join(cls.SECTION_PATTERNS)
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))

        if not matches:
            return [{
                "section_label": "FULL_DOCUMENT",
                "section_title": "Full Document",
                "section_text": text,
                "section_order": 1
            }]

        sections = []

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            section_title = match.group(0)
            section_text = text[start:end].strip()

            sections.append({
                "section_label": section_title[:30],
                "section_title": section_title,
                "section_text": section_text,
                "section_order": i + 1
            })

        return sections