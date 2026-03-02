import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.postgres import Base


class FormatReviewSession(Base):
    __tablename__ = "format_review_sessions"
    __table_args__ = (UniqueConstraint("user_id", "session_key", name="uq_format_review_sessions_user_session_key"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_key = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FormatReviewTask(Base):
    __tablename__ = "format_review_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_key = Column(String(64), nullable=False, index=True)
    upload_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    rule_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    status = Column(String(32), default="queued", nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FormatReviewUpload(Base):
    __tablename__ = "format_review_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_key = Column(String(64), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=True)
    size = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    status = Column(String(32), default="uploading", nullable=False, index=True)
    uploaded_parts = Column(JSONB, nullable=True)
    sha256 = Column(String(128), nullable=True)
    storage_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FormatReviewHistory(Base):
    __tablename__ = "format_review_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_key = Column(String(64), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    paper_title = Column(String(512), nullable=True)
    filename = Column(String(512), nullable=True)
    status = Column(String(32), default="done", nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)
    issues_count = Column(Integer, nullable=True)
    report_markdown = Column(Text, nullable=True)
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FormatReviewFixTask(Base):
    __tablename__ = "format_review_fix_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    history_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(String(32), default="queued", nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)
    result_path = Column(String(1024), nullable=True)
    error = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DownloadToken(Base):
    __tablename__ = "download_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    path = Column(String(1024), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
