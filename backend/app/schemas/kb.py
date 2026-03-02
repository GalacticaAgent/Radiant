from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class CrawlJobResponse(BaseModel):
    id: UUID
    job_type: str
    target_type: str
    target_id: Optional[UUID]
    status: str
    attempts: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CrawlEventResponse(BaseModel):
    id: UUID
    job_id: UUID
    level: str
    message: str
    payload: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    status: str
    jobs: List[CrawlJobResponse]


class SimilarPaperItem(BaseModel):
    paper_id: str
    title: str
    score: float


class SimilarPapersResponse(BaseModel):
    paper_id: str
    items: List[SimilarPaperItem]
    total: int

