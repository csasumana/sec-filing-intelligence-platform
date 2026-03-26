# SEC Filing Intelligence Platform

Production-grade RAG system for SEC 10-K analysis, structured extraction, and cross-filing comparison using FastAPI, PostgreSQL + pgvector, Sentence Transformers, Cross-Encoder reranking, Gemini, and Streamlit.

## Overview

This project ingests SEC filings (10-K / 10-Q style HTML filings), parses and sections them, chunks the content, stores embeddings in PostgreSQL with pgvector, retrieves semantically relevant evidence, reranks with a cross-encoder, and generates grounded answers with citations.

It also supports:

- **Structured field extraction** (risk factors, legal proceedings, share repurchases, etc.)
- **Cross-filing comparison** (e.g., compare Apple 2024 vs 2025 risk factors)
- **Evidence traceability** with chunk-level citations
- **Production-style API + UI architecture**

---

## Why this project matters

Most RAG portfolio projects are generic “chat with your PDF” demos.

This project is different because it focuses on **financial filings**, where:
- retrieval quality matters,
- evidence grounding matters,
- structured extraction matters,
- and comparing disclosures across filings creates real business value.



---

## Features

### Core capabilities
- SEC filing ingestion from public EDGAR URLs
- Inline XBRL / SEC URL normalization
- HTML filing parsing and cleanup
- Section-aware chunking (Item 1A, Item 3, Item 7, etc.)
- Embedding generation using Sentence Transformers
- PostgreSQL + pgvector vector storage
- Semantic retrieval over filing chunks
- Cross-encoder reranking for improved relevance
- Grounded Q&A with citations
- “Insufficient evidence” fallback behavior

### Advanced capabilities
- Structured field extraction (`/extract`)
- Cross-filing comparison (`/compare`)
- Field-level evidence + citations
- Clean re-ingestion (delete old filing before reinsert)
- Streamlit UI for end-to-end demo

---

## Tech Stack

- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Database:** PostgreSQL + pgvector
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`)
- **Reranker:** Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- **LLM:** Gemini API
- **Parsing:** BeautifulSoup / HTML parsing
- **HTTP:** requests
- **Environment:** Python, VS Code, Windows PowerShell

---

## System Architecture

```text
SEC Filing URL
   ↓
Fetch + Normalize URL
   ↓
HTML Parsing + Text Cleanup
   ↓
Section Splitting (Item 1A / Item 3 / Item 7 / etc.)
   ↓
Chunking
   ↓
Embedding Generation
   ↓
PostgreSQL + pgvector
   ↓
Semantic Retrieval
   ↓
Cross-Encoder Reranking
   ↓
Grounded Generation / Structured Extraction / Filing Comparison
   ↓
FastAPI Response + Streamlit UI

API Endpoints
1. Ingest Filing

POST /filings/ingest

Ingests a filing from a public SEC URL, parses it, chunks it, embeds it, and stores it in PostgreSQL.

2. Query Filing

POST /query

Answers grounded questions about a filing using retrieval + reranking + Gemini.

Example use case:

“What are the main risk factors related to competition and supply chain?”
3. Extract Structured Fields

POST /extract

Extracts structured, field-aware information from a filing.

Supported fields:

material_risk_factors_summary
legal_proceedings_summary
business_segments
share_repurchase_mention
total_revenue_mention
net_income_mention
4. Compare Two Filings

POST /compare

Compares two filings for a focused disclosure area.

Supported focuses:

risk_factors
legal_proceedings
capital_return
business_segments
financial_performance

Example use case:

Compare Apple 2024 vs 2025 risk factor disclosures
Example Demo Flow
Ingest Apple 2025 10-K
Ask:
“What are the main risk factors related to competition and supply chain?”
Extract:
material_risk_factors_summary
share_repurchase_mention
Ingest Apple 2024 10-K
Compare:
risk_factors
Example Filing IDs Used in Demo
AAPL_10-K_000032019325000079
AAPL_10-K_000032019324000123
Project Structure
project_2_sec_filing_rag/
│
├── app/
│   ├── api/
│   │   └── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── prompts.py
│   ├── generation/
│   │   ├── answer_generator.py
│   │   ├── extractor.py
│   │   └── comparator.py
│   ├── indexing/
│   │   ├── embedder.py
│   │   └── vector_store.py
│   ├── ingestion/
│   │   └── filing_parser.py
│   ├── retrieval/
│   │   ├── reranker.py
│   │   └── citation_builder.py
│   ├── services/
│   │   └── ingest_service.py
│   └── ui/
│       └── streamlit_app.py
│
├── data/
│   └── raw_filings/
│
├── db/
│   └── init.sql
│
├── .env
├── requirements.txt
└── README.md
Setup Instructions
1. Create virtual environment
python -m venv .venv
2. Activate environment

Windows PowerShell

.venv\Scripts\Activate.ps1
3. Install dependencies
pip install -r requirements.txt
4. Start PostgreSQL + pgvector

Make sure:

PostgreSQL is running
pgvector extension is enabled
5. Initialize database schema
CREATE DATABASE sec_rag_db;
\c sec_rag_db
CREATE EXTENSION IF NOT EXISTS vector;
\i 'db/init.sql'
6. Configure .env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sec_rag_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

GEMINI_API_KEY=your_key_here
SEC_USER_AGENT=YourName your_email@example.com
7. Run FastAPI
uvicorn app.api.main:app --reload
8. Run Streamlit
streamlit run app/ui/streamlit_app.py
Key Design Decisions
Used pgvector instead of an in-memory vector store for production-style persistence
Used section-aware chunking to preserve SEC filing structure
Added cross-encoder reranking to improve retrieval precision
Added field-aware extraction rather than naive “extract everything”
Added cross-filing comparison to support disclosure drift analysis
Added retry + fallback behavior for Gemini model instability
Future Improvements
Better table-aware numeric extraction from financial statements
Hybrid retrieval (BM25 + vector)
Metadata filters (ticker / form type / filing year)
Evaluation benchmark set for retrieval quality
Dockerized deployment
Cloud deployment (Render / Railway / Fly.io)
Multi-filing portfolio / watchlist analysis