"""
Private Graph 私有知识图谱相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class NodeData(BaseModel):
    """节点数据"""
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    labels: List[str] = Field(default_factory=list, description="节点标签")


class EdgeData(BaseModel):
    """关系数据"""
    relationship_type: str = Field(..., description="关系类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")


class PrivateGraphCreate(BaseModel):
    """创建私有图谱请求"""
    name: str = Field(..., description="图谱名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="图谱描述", max_length=500)
    is_public: bool = Field(default=False, description="是否公开")


class PrivateGraphUpdate(BaseModel):
    """更新私有图谱请求"""
    name: Optional[str] = Field(None, description="图谱名称")
    description: Optional[str] = Field(None, description="图谱描述")
    is_public: Optional[bool] = Field(None, description="是否公开")


class NodeCreateRequest(BaseModel):
    """添加节点请求"""
    node_id: str = Field(..., description="节点ID", min_length=1)
    node_type: str = Field(..., description="节点类型", min_length=1)
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="节点属性")


class NodeResponse(BaseModel):
    """节点响应"""
    id: str
    type: str
    graph_id: str
    properties: Dict[str, Any]
    created_at: datetime


class EdgeCreateRequest(BaseModel):
    """添加关系请求"""
    source_id: str = Field(..., description="源节点ID")
    target_id: str = Field(..., description="目标节点ID")
    relationship_type: str = Field(..., description="关系类型", min_length=1)
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="关系属性")


class EdgeResponse(BaseModel):
    """关系响应"""
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    graph_id: str
    properties: Dict[str, Any]
    created_at: datetime


class PrivateGraphResponse(BaseModel):
    """私有图谱响应"""
    id: str
    owner_id: str
    name: str
    description: Optional[str]
    is_public: bool
    node_count: int = 0
    edge_count: int = 0
    created_at: datetime
    updated_at: datetime


class PrivateGraphDetailResponse(PrivateGraphResponse):
    """私有图谱详细响应"""
    nodes: List[NodeResponse] = []
    edges: List[EdgeResponse] = []


class GraphSearchRequest(BaseModel):
    """图谱搜索请求"""
    query: str = Field(..., description="搜索查询", min_length=1)
    node_type: Optional[str] = Field(None, description="节点类型过滤")
    limit: int = Field(default=20, ge=1, le=100, description="结果数量限制")


class GraphSearchResult(BaseModel):
    """图谱搜索结果"""
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
    total: int
