import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.postgres import Base


class FormatRule(Base):
    __tablename__ = "format_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    pinned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FormatRuleVersion(Base):
    __tablename__ = "format_rule_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("format_rules.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FormatRuleFile(Base):
    __tablename__ = "format_rule_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    size = Column(Integer, nullable=False)
    mime_type = Column(String(128), nullable=True)
    sha256 = Column(String(128), nullable=True)
    storage_path = Column(String(1024), nullable=True)
    status = Column(String(32), default="uploaded", nullable=False, index=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

