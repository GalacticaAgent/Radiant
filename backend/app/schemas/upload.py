from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UploadInitRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=64)
    filename: str = Field(..., min_length=1, max_length=512)
    size: int = Field(..., ge=1)
    mime_type: Optional[str] = None


class UploadInitResult(BaseModel):
    upload_id: UUID
    chunk_size: int
    expected_parts: int


class UploadStatusResult(BaseModel):
    upload_id: UUID
    status: str
    uploaded_parts: List[int]
    chunk_size: int
    size: int
    expected_parts: int
    missing_parts: List[int]


class UploadCompleteResult(BaseModel):
    upload_id: UUID
    status: str
