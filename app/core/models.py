from sqlalchemy import Column, Integer, Text, Date, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Filing(Base):
    __tablename__ = "filings"

    filing_id = Column(Text, primary_key=True)
    company_name = Column(Text)
    ticker = Column(Text)
    cik = Column(Text)
    form_type = Column(Text)
    filing_date = Column(Date)
    accession_number = Column(Text)
    source_url = Column(Text)
    local_path = Column(Text)
    raw_text = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


class FilingSection(Base):
    __tablename__ = "filing_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Text, ForeignKey("filings.filing_id", ondelete="CASCADE"))
    section_label = Column(Text)
    section_title = Column(Text)
    section_text = Column(Text)
    section_order = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())


class FilingChunk(Base):
    __tablename__ = "filing_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Text, ForeignKey("filings.filing_id", ondelete="CASCADE"))
    section_id = Column(Integer, ForeignKey("filing_sections.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    chunk_text = Column(Text)
    token_estimate = Column(Integer)
    # embedding stored via raw SQL insert/update for now
    created_at = Column(TIMESTAMP, server_default=func.now())