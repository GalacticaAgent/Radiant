"""
论文数据模型
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.db.postgres import Base


class Paper(Base):
    """
    论文模型 - 存储用户上传的论文信息
    """
    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 论文基本信息
    title = Column(String(500), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)

    # 论文内容
    content = Column(Text, nullable=True)  # 提取的文本内容
    abstract = Column(Text, nullable=True)  # 摘要

    # 元数据
    paper_metadata = Column(JSONB, nullable=True)  # 作者、机构等信息

    # 版本管理
    version = Column(Integer, default=1, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("papers.id"), nullable=True)  # 父版本ID

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaperReview(Base):
    """
    审稿意见模型
    """
    __tablename__ = "paper_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 审稿人信息
    reviewer_id = Column(String(100), nullable=True)  # 知识图谱中的审稿人ID
    reviewer_name = Column(String(200), nullable=True)
    reviewer_profile = Column(Text, nullable=True)  # 审稿人画像

    # 审稿意见
    review_content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 评分 1-10

    # 详细意见
    strengths = Column(ARRAY(Text), nullable=True)  # 优点列表
    weaknesses = Column(ARRAY(Text), nullable=True)  # 缺点列表
    suggestions = Column(ARRAY(Text), nullable=True)  # 修改建议列表

    # 元数据
    review_metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
