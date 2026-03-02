"""
对话相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")
    search_graph: bool = Field(True, description="是否搜索知识图谱")


class ReferenceItem(BaseModel):
    """引用项 Schema"""
    type: str = Field(..., description="引用类型 (paper/person/code)")
    id: str = Field(..., description="节点ID")
    title: str = Field(..., description="标题")
    url: Optional[str] = Field(None, description="URL")


class ChatResponse(BaseModel):
    """聊天响应 Schema"""
    message_id: str
    content: str
    references: Optional[List[ReferenceItem]] = []
    session_id: str


class ConversationMessage(BaseModel):
    """对话消息 Schema"""
    role: str  # user, assistant, system
    content: str
    references: Optional[dict] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ConversationHistoryResponse(BaseModel):
    """对话历史列表响应"""
    session_id: str
    messages: List[ConversationMessage]
    total: int


class SessionSchema(BaseModel):
    """会话 Schema"""
    id: str
    title: str
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RenameSessionRequest(BaseModel):
    """重命名会话请求"""
    title: str = Field(..., min_length=1, max_length=255)


class PinSessionRequest(BaseModel):
    """置顶会话请求"""
    pinned: bool


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionSchema]


class AppendMessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64, description="会话ID")
    role: str = Field(..., description="角色（user/assistant/system）")
    content: str = Field(..., min_length=1, max_length=20000, description="消息内容")
    references: Optional[Dict[str, Any]] = Field(None, description="引用数据")


class AppendMessageResponse(BaseModel):
    session_id: str
    created_at: str
