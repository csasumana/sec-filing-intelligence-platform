CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS filings (
    filing_id TEXT PRIMARY KEY,
    company_name TEXT,
    ticker TEXT,
    cik TEXT,
    form_type TEXT,
    filing_date DATE,
    accession_number TEXT,
    source_url TEXT,
    local_path TEXT,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS filing_sections (
    id SERIAL PRIMARY KEY,
    filing_id TEXT REFERENCES filings(filing_id) ON DELETE CASCADE,
    section_label TEXT,
    section_title TEXT,
    section_text TEXT,
    section_order INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS filing_chunks (
    id SERIAL PRIMARY KEY,
    filing_id TEXT REFERENCES filings(filing_id) ON DELETE CASCADE,
    section_id INT REFERENCES filing_sections(id) ON DELETE CASCADE,
    chunk_index INT,
    chunk_text TEXT,
    token_estimate INT,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_filing_sections_filing_id
ON filing_sections(filing_id);

CREATE INDEX IF NOT EXISTS idx_filing_chunks_filing_id
ON filing_chunks(filing_id);