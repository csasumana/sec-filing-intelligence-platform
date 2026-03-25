from pathlib import Path
from urllib.parse import urlparse, parse_qs
import httpx

from app.core.config import settings


class SECFetcher:
    def __init__(self):
        self.headers = {
            "User-Agent": settings.SEC_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }

    def normalize_sec_url(self, filing_url: str) -> str:
        """
        Convert SEC inline XBRL viewer URLs like:
        https://www.sec.gov/ix?doc=/Archives/...
        into raw filing URLs like:
        https://www.sec.gov/Archives/...
        """
        parsed = urlparse(filing_url)

        if parsed.path == "/ix":
            query_params = parse_qs(parsed.query)
            doc_values = query_params.get("doc", [])
            if doc_values:
                doc_path = doc_values[0]
                if doc_path.startswith("/Archives/"):
                    return f"https://www.sec.gov{doc_path}"

        return filing_url

    def download_filing_html(self, filing_url: str, output_filename: str) -> Path:
        raw_dir = Path(settings.DATA_DIR) / "raw_filings"
        raw_dir.mkdir(parents=True, exist_ok=True)

        output_path = raw_dir / output_filename
        normalized_url = self.normalize_sec_url(filing_url)

        with httpx.Client(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            response = client.get(normalized_url)
            response.raise_for_status()

        output_path.write_text(response.text, encoding="utf-8")
        return output_path