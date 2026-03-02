"""
知识图谱 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.db.postgres import get_db
from app.db.neo4j import get_neo4j
from app.api.deps import get_current_user
from app.models.user import User
from app.services.graph_service import GraphService
from app.db.neo4j import Neo4jConnection

router = APIRouter()


class SubgraphResponse(BaseModel):
    """子图响应"""
    nodes: List[dict]
    edges: List[dict]


class NodeResponse(BaseModel):
    """节点详情响应"""
    id: str
    type: str
    properties: dict
    relationships: List[dict] = []


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[dict]
    total: int


def get_graph_service(
    neo4j_conn: Neo4jConnection = Depends(get_neo4j)
) -> GraphService:
    """获取图谱服务"""
    return GraphService(neo4j_conn)


@router.get("/search", response_model=SearchResponse)
def search_nodes(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    type: Optional[str] = Query(None, description="节点类型"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    搜索知识图谱节点

    - **q**: 搜索关键词（必需）
    - **type**: 节点类型（可选，Paper/Person/Organization/Code）
    - **limit**: 返回结果数量（1-100，默认20）
    """
    results = graph_service.search_nodes(q, node_type=type, limit=limit)
    return SearchResponse(results=results, total=len(results))


@router.get("/subgraph", response_model=SubgraphResponse)
def get_subgraph(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    depth: int = Query(2, ge=1, le=5, description="图谱深度"),
    limit: int = Query(100, ge=10, le=500, description="节点数量限制"),
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    current_user: User = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    提取知识图谱子图

    - **query**: 搜索关键词（必需）
    - **depth**: 图谱搜索深度，默认2（1-5）
    - **limit**: 返回节点数量限制，默认100（10-500）
    - **node_type**: 节点类型过滤（可选）

    返回包含节点和边的子图数据，可用于前端可视化。
    """
    subgraph = graph_service.get_subgraph(query, depth, limit, node_type)
    return SubgraphResponse(nodes=subgraph["nodes"], edges=subgraph["edges"])


@router.get("/node/{node_id}", response_model=NodeResponse)
def get_node(
    node_id: str = Path(..., description="节点ID"),
    current_user: User = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    获取节点详细信息

    - **node_id**: 节点ID

    返回节点的详细信息和相关关系。
    """
    node_info = graph_service.get_node_by_id(node_id)

    if not node_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )

    node_data = node_info.get("n", {})
    return NodeResponse(
        id=node_data.get("id"),
        type=GraphService._get_node_type(node_data),
        properties=node_data,
        relationships=node_info.get("relationships", [])
    )


@router.get("/researcher/{researcher_id}/papers", response_model=list)
def get_researcher_papers(
    researcher_id: str = Path(..., description="研究者ID"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    获取研究者发表的论文

    - **researcher_id**: 研究者ID
    - **limit**: 返回数量限制
    """
    papers = graph_service.get_researcher_papers(researcher_id, limit)

    if not papers:
        return []

    return papers[:limit]


@router.get("/paper/{paper_id}/related", response_model=list)
def get_related_papers(
    paper_id: str = Path(..., description="论文ID"),
    depth: int = Query(2, ge=1, le=3),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    获取相关论文

    - **paper_id**: 论文ID
    - **depth**: 搜索深度（1-3）
    - **limit**: 返回数量限制
    """
    papers = graph_service.get_related_papers(paper_id, depth, limit)

    if not papers:
        return []

    return papers[:limit]
