from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.postgres import Base


class VirtualReviewer(Base):
    __tablename__ = "virtual_reviewers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)  # semantic_scholar | arxiv | github | mixed
    external_id = Column(String(200), nullable=False)

    name = Column(String(200), nullable=False)
    affiliation = Column(String(500), nullable=True)

    h_index = Column(Integer, nullable=True)
    citation_count = Column(Integer, nullable=True)
    paper_count = Column(Integer, nullable=True)

    profile_text = Column(Text, nullable=True)
    top_papers = Column(JSONB, nullable=True)
    talk_links = Column(JSONB, nullable=True)
    raw_profile = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_virtual_reviewers_source_external_id"),
    )


class PaperReviewerCandidate(Base):
    __tablename__ = "paper_reviewer_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("virtual_reviewers.id", ondelete="CASCADE"), nullable=False)

    rank = Column(Integer, default=0, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    rationale = Column(String(800), nullable=True)
    matched_keywords = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("paper_id", "reviewer_id", name="uq_paper_reviewer_candidates_paper_id_reviewer_id"),
    )

