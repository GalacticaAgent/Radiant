"""
Idea 验证相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class IdeaValidationRequest(BaseModel):
    """Idea验证请求"""
    idea: str = Field(..., min_length=10, max_length=2000, description="研究想法")
    background: Optional[str] = Field(None, description="背景信息")


class RelatedPaper(BaseModel):
    """相关论文"""
    id: str
    title: str
    authors: List[str]
    year: Optional[int]
    relevance: float  # 相关度分数 0-1


class IdeaValidationResult(BaseModel):
    """Idea验证结果"""
    feasibility_score: float  # 可行性评分 0-10
    innovation_score: float  # 创新性评分 0-10
    technical_difficulty: str  # 技术难度：低/中/高
    estimated_time: str  # 预计时间：1个月/3个月/6个月/1年+

    strengths: List[str]  # 优势
    challenges: List[str]  # 挑战
    recommendations: List[str]  # 建议

    related_papers: List[RelatedPaper]  # 相关论文
    research_directions: List[str]  # 相关研究方向

    detailed_analysis: str  # 详细分析


class IdeaListResponse(BaseModel):
    """Idea列表响应"""
    ideas: List[Dict[str, Any]]
    total: int
