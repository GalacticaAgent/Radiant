"""
Research 调研相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchSource(str, Enum):
    """调研数据源"""
    KNOWLEDGE_GRAPH = "knowledge_graph"
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"


class ResearchRequest(BaseModel):
    """调研请求"""
    query: str = Field(..., description="调研主题或问题", min_length=1)
    sources: List[ResearchSource] = Field(
        default=[ResearchSource.KNOWLEDGE_GRAPH],
        description="数据源列表"
    )
    max_papers: int = Field(
        default=50,
        ge=1,
        le=200,
        description="最大论文数量"
    )
    filters: Optional[dict] = Field(
        default=None,
        description="过滤条件（如年份、作者等）"
    )


class PaperSummary(BaseModel):
    """论文摘要"""
    id: str
    title: str
    authors: List[str]
    year: Optional[int] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = Field(ge=0, le=1, description="相关度评分")
    key_findings: Optional[str] = None


class ResearchResult(BaseModel):
    """调研结果"""
    task_id: str
    query: str
    papers: List[PaperSummary]
    total_found: int
    summary: str = Field(description="调研总结")
    key_trends: List[str] = Field(description="关键趋势")
    research_gaps: List[str] = Field(description="研究空白")
    recommendations: List[str] = Field(description="建议")
    completed_at: datetime


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: str
    status: TaskStatus
    query: str
    created_at: datetime
    updated_at: datetime
    progress: int = Field(ge=0, le=100, description="任务进度百分比")
    message: Optional[str] = None
    error: Optional[str] = None


class ResearchStartResponse(BaseModel):
    """调研启动响应"""
    task_id: str
    status: TaskStatus
    message: str
