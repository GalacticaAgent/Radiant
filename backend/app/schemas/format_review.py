from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FormatReviewStartRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=64)
    upload_id: Optional[UUID] = None
    rule_id: Optional[UUID] = None
    paper_title: Optional[str] = None
    filename: Optional[str] = None


class FormatReviewStartResult(BaseModel):
    task_id: UUID


class FormatReviewTaskResult(BaseModel):
    task_id: UUID
    session_id: str
    status: str
    progress: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    result: Optional[Any] = None


class FormatReviewHistoryItem(BaseModel):
    history_id: UUID
    session_id: str
    paper_title: Optional[str] = None
    filename: Optional[str] = None
    status: str
    duration_ms: Optional[int] = None
    issues_count: Optional[int] = None
    created_at: datetime


class FormatReviewHistoryList(BaseModel):
    total: int
    items: List[FormatReviewHistoryItem]


class FormatReviewHistorySaveRequest(BaseModel):
    task_id: UUID


class FormatReviewHistorySaveResult(BaseModel):
    history_id: UUID


class FormatReviewAutoFixRequest(BaseModel):
    history_id: UUID


class FormatReviewAutoFixResult(BaseModel):
    fix_task_id: UUID


class FormatReviewFixTaskResult(BaseModel):
    fix_task_id: UUID
    status: str
    progress: int
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None
