import re
from bs4 import BeautifulSoup


class FilingParser:
    @staticmethod
    def html_to_text(html_content: str) -> str:
        soup = BeautifulSoup(html_content, "lxml")

        # Remove obvious non-content tags
        for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
            tag.decompose()

        # Remove inline XBRL / metadata-ish tags if present
        # We don't want to be overly aggressive, but these often pollute text extraction
        xbrl_like_tags = [
            "ix:header",
            "ix:hidden",
            "ix:nonnumeric",
            "ix:nonfraction",
            "xbrli:context",
            "xbrli:unit",
        ]
        for tag_name in xbrl_like_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        text = soup.get_text(separator="\n")

        # Split into lines and strip
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]

        cleaned_lines = []
        for line in lines:
            # Skip pure taxonomy / namespace / XBRL junk
            if re.match(r"^(us-gaap:|dei:|xbrli:|iso4217:|aapl:)", line, flags=re.IGNORECASE):
                continue

            if re.match(r"^http://fasb\.org/", line, flags=re.IGNORECASE):
                continue

            if re.match(r"^https?://xbrl\.", line, flags=re.IGNORECASE):
                continue

            # Skip obvious machine-like identifiers
            if re.match(r"^[A-Za-z0-9_.:-]+Member$", line):
                continue

            # Skip isolated technical period markers
            if line in {"P1Y", "P3M", "P6M", "P9M", "FY", "Q1", "Q2", "Q3", "Q4"}:
                continue

            # Skip lines that are mostly symbol soup / too little natural language
            alpha_chars = sum(c.isalpha() for c in line)
            if len(line) > 0 and alpha_chars / max(len(line), 1) < 0.25 and len(line) > 20:
                continue

            cleaned_lines.append(line)

        # Collapse excessive blank structure by rejoining
        cleaned_text = "\n".join(cleaned_lines)

        # Optional: normalize too many blank lines if any remain
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        return cleaned_text