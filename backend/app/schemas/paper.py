"""
论文相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class PaperBase(BaseModel):
    """论文基础模型"""
    title: Optional[str] = None
    abstract: Optional[str] = None


class PaperUploadResponse(BaseModel):
    """论文上传响应"""
    id: UUID
    filename: str
    title: Optional[str]
    file_size: int
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaperResponse(BaseModel):
    """论文详细信息响应"""
    id: UUID
    user_id: UUID
    title: Optional[str]
    filename: str
    file_size: int
    abstract: Optional[str]
    paper_metadata: Optional[Dict[str, Any]]
    version: int
    parent_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """论文列表响应"""
    papers: List[PaperResponse]
    total: int


class ReviewerRecommendation(BaseModel):
    """审稿人推荐"""
    id: str
    name: str
    affiliation: str
    research_interests: List[str] = []
    h_index: int = 0
    match_count: int
    matched_keywords: List[str]


class ReviewerRecommendationResponse(BaseModel):
    """审稿人推荐响应"""
    reviewers: List[ReviewerRecommendation]
    total: int


class ReviewerCandidatePaper(BaseModel):
    paper_id: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: int = 0
    url: Optional[str] = None


class ReviewerCandidate(BaseModel):
    id: str
    name: str
    affiliation: str
    h_index: int = 0
    citation_count: int = 0
    paper_count: int = 0
    match_score: int = 0
    matched_keywords: List[str] = []
    rationale: Optional[str] = None
    source: str
    external_id: str
    top_papers: List[ReviewerCandidatePaper] = []


class ReviewerCandidateResponse(BaseModel):
    candidates: List[ReviewerCandidate]
    total: int


class GenerateReviewRequest(BaseModel):
    """生成审稿意见请求"""
    reviewer_ids: List[str] = Field(..., description="审稿人ID列表")
    generate_suggestions: bool = Field(default=True, description="是否生成修改建议")


class SeedDomainExpertsRequest(BaseModel):
    query: str = Field(..., description="领域/关键词（建议英文）")
    per_page: int = Field(default=25, ge=1, le=25)
    max_authors: int = Field(default=200, ge=1, le=2000)


class SeedDomainExpertsResponse(BaseModel):
    status: str
    task_id: Optional[str] = None


class ReviewResponse(BaseModel):
    """审稿意见响应"""
    id: UUID
    paper_id: UUID
    reviewer_id: Optional[str]
    reviewer_name: str
    reviewer_profile: str
    review_content: str
    rating: Optional[int]
    confidence: Optional[str] = None
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    suggestions: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """审稿意见列表响应"""
    reviews: List[ReviewResponse]
    total: int


class ModificationSuggestion(BaseModel):
    """修改建议"""
    section: str
    issue: str
    suggestion: str
    priority: str  # 高/中/低


class SuggestionsResponse(BaseModel):
    """修改建议响应"""
    suggestions: List[ModificationSuggestion]
    total: int


class VersionResponse(BaseModel):
    """版本信息响应"""
    id: UUID
    version: int
    title: Optional[str]
    filename: str
    parent_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class VersionListResponse(BaseModel):
    """版本列表响应"""
    versions: List[VersionResponse]
    current_version: int
    total: int


class PaperPolishRequest(BaseModel):
    mode: str = Field(default="abstract_only", description="abstract_only 或 full")
    selected_suggestions: Optional[List[str]] = Field(default=None, description="选中的建议文本列表")


class PaperPolishResponse(BaseModel):
    paper_id: UUID
    mode: str
    original_abstract: str
    polished_abstract: str
    diff: str
    applied_suggestions: List[str]
    generated_at: datetime


class PaperReviewReportResponse(BaseModel):
    paper_id: UUID
    markdown: str
    generated_at: datetime


class FormatReviewRequest(BaseModel):
    scope: str = Field(default="auto", description="auto / abstract / full")
    language: str = Field(default="auto", description="auto / zh / en")


class FormatIssue(BaseModel):
    severity: str = Field(..., description="critical / major / minor / cosmetic")
    position: str
    description: str
    suggestion: str
    evidence: Optional[str] = None


class PaperFormatReviewResponse(BaseModel):
    paper_id: UUID
    markdown: str
    issues: Optional[List[FormatIssue]] = None
    rule_issues: Optional[List[FormatIssue]] = None
    llm_issues: Optional[List[FormatIssue]] = None
    auto_metrics: Optional[Dict[str, Any]] = None
    overall_grade: Optional[str] = None
    priority: Optional[str] = None
    generated_at: datetime


class AdhocFormatReviewResponse(BaseModel):
    markdown: str
    issues: Optional[List[FormatIssue]] = None
    rule_issues: Optional[List[FormatIssue]] = None
    llm_issues: Optional[List[FormatIssue]] = None
    auto_metrics: Optional[Dict[str, Any]] = None
    overall_grade: Optional[str] = None
    priority: Optional[str] = None
    generated_at: datetime
