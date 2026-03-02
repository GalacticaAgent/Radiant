from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.config import settings

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:
    Vector = None

from app.db.postgres import Base


class Author(Base):
    __tablename__ = "authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)
    external_id = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)

    aliases = Column(JSONB, nullable=True)
    affiliations = Column(JSONB, nullable=True)
    homepage = Column(Text, nullable=True)
    url = Column(Text, nullable=True)

    h_index = Column(Integer, nullable=True)
    citation_count = Column(Integer, nullable=True)
    paper_count = Column(Integer, nullable=True)

    raw_profile = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("authors.id", ondelete="CASCADE"), nullable=False)
    author_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PaperTopic(Base):
    __tablename__ = "paper_topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ExternalPaper(Base):
    __tablename__ = "external_papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)
    external_id = Column(String(200), nullable=False)

    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    venue = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    external_ids = Column(JSONB, nullable=True)
    fields_of_study = Column(JSONB, nullable=True)
    citation_count = Column(Integer, nullable=True)

    raw = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_type = Column(String(30), nullable=False)
    object_id = Column(UUID(as_uuid=True), nullable=False)
    model = Column(String(100), nullable=False)
    dim = Column(Integer, nullable=False)
    vector = Column(Vector(settings.PGVECTOR_DIM), nullable=True) if (settings.PGVECTOR_ENABLED and Vector) else Column(JSONB, nullable=True)
    vector_jsonb = Column(JSONB, nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)
    target_type = Column(String(30), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="queued")
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrawlEvent(Base):
    __tablename__ = "crawl_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
