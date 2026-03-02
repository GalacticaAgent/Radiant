from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RuleUploadResult(BaseModel):
    file_id: UUID


class RuleGenerateRequest(BaseModel):
    file_id: UUID


class RuleGenerateResult(BaseModel):
    task_id: UUID


class RuleTaskResult(BaseModel):
    task_id: UUID
    status: str
    rule_id: Optional[UUID] = None
    error: Optional[str] = None


class RuleItem(BaseModel):
    rule_id: UUID
    name: str
    pinned: bool
    version: int
    created_at: datetime


class RuleListResult(BaseModel):
    items: List[RuleItem]


class RuleRenameRequest(BaseModel):
    rule_id: UUID
    name: str = Field(..., min_length=1, max_length=30)


class RulePinRequest(BaseModel):
    rule_id: UUID
    pinned: bool = True


class RuleSkillRenameRequest(BaseModel):
    rule_id: UUID
    skill_name: str = Field(..., min_length=3, max_length=64)


class RuleVersionItem(BaseModel):
    version: int
    created_at: datetime


class RuleVersionListResult(BaseModel):
    rule_id: UUID
    versions: List[RuleVersionItem]


class RuleRollbackRequest(BaseModel):
    version: int = Field(..., ge=1)


class RuleRollbackResult(BaseModel):
    rule_id: UUID
    version: int
