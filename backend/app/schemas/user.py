"""
用户相关的 Pydantic Schemas
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")


class UserCreate(UserBase):
    """用户创建 Schema"""
    password: str = Field(..., min_length=8, max_length=100, description="密码（至少8位）")


class UserUpdate(BaseModel):
    """用户更新 Schema"""
    email: Optional[EmailStr] = None
    deepseek_api_key: Optional[str] = None


class UserInDB(UserBase):
    """数据库中的用户 Schema"""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """用户响应 Schema（返回给客户端）"""
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token 响应 Schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Token 负载 Schema"""
    sub: Optional[str] = None  # subject (user_id)
    exp: Optional[int] = None  # expiration time
    type: Optional[str] = None  # token type (access/refresh)
