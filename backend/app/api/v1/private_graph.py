"""
Private Graph 私有知识图谱 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.private_graph_service import PrivateGraphService
from app.schemas.private_graph import (
    PrivateGraphCreate,
    PrivateGraphUpdate,
    PrivateGraphResponse,
    PrivateGraphDetailResponse,
    NodeCreateRequest,
    NodeResponse,
    EdgeCreateRequest,
    EdgeResponse,
    GraphSearchRequest,
    GraphSearchResult
)

router = APIRouter(tags=["private_graph"])


@router.post("/", response_model=PrivateGraphResponse)
def create_private_graph(
    request: PrivateGraphCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建私有图谱

    - **name**: 图谱名称（必填）
    - **description**: 图谱描述（可选）
    - **is_public**: 是否公开（默认: false）

    返回创建的图谱信息
    """
    try:
        graph = PrivateGraphService.create_graph(
            owner_id=str(current_user.id),
            name=request.name,
            description=request.description,
            is_public=request.is_public
        )
        return graph
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建私有图谱失败: {str(e)}"
        )


@router.get("/list", response_model=List[PrivateGraphResponse])
def list_graphs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    列出用户的所有私有图谱

    返回当前用户创建的所有图谱列表
    """
    return PrivateGraphService.list_user_graphs(str(current_user.id))


@router.get("/{graph_id}", response_model=PrivateGraphDetailResponse)
def get_private_graph(
    graph_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取私有图谱详细信息

    - **graph_id**: 图谱ID

    返回图谱的完整信息，包括所有节点和关系
    """
    graph = PrivateGraphService.get_graph_detail(graph_id, str(current_user.id))

    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图谱不存在或无权限访问: {graph_id}"
        )

    return graph


@router.put("/{graph_id}", response_model=PrivateGraphResponse)
def update_private_graph(
    graph_id: str,
    request: PrivateGraphUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新私有图谱信息

    - **graph_id**: 图谱ID
    - **name**: 新名称（可选）
    - **description**: 新描述（可选）
    - **is_public**: 新的公开状态（可选）

    返回更新后的图谱信息
    """
    graph = PrivateGraphService.update_graph(
        graph_id=graph_id,
        owner_id=str(current_user.id),
        name=request.name,
        description=request.description,
        is_public=request.is_public
    )

    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图谱不存在或无权限修改: {graph_id}"
        )

    return graph


@router.delete("/{graph_id}")
def delete_private_graph(
    graph_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除私有图谱

    - **graph_id**: 图谱ID

    删除整个图谱及其所有节点和关系
    """
    success = PrivateGraphService.delete_graph(graph_id, str(current_user.id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图谱不存在或无权限删除: {graph_id}"
        )

    return {"message": "图谱已删除"}


@router.post("/{graph_id}/node", response_model=NodeResponse)
def add_node(
    graph_id: str,
    request: NodeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加节点到私有图谱

    - **graph_id**: 图谱ID
    - **node_id**: 节点ID（必填）
    - **node_type**: 节点类型（必填）
    - **properties**: 节点属性（可选）

    返回添加的节点信息
    """
    node = PrivateGraphService.add_node(
        graph_id=graph_id,
        owner_id=str(current_user.id),
        node_id=request.node_id,
        node_type=request.node_type,
        properties=request.properties
    )

    if not node:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="添加节点失败：图谱不存在、无权限或节点已存在"
        )

    return node


@router.delete("/{graph_id}/node/{node_id}")
def remove_node(
    graph_id: str,
    node_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从私有图谱中删除节点

    - **graph_id**: 图谱ID
    - **node_id**: 节点ID

    删除节点及其相关的所有关系
    """
    success = PrivateGraphService.remove_node(graph_id, str(current_user.id), node_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在或无权限删除"
        )

    return {"message": "节点已删除"}


@router.post("/{graph_id}/edge", response_model=EdgeResponse)
def add_edge(
    graph_id: str,
    request: EdgeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加关系到私有图谱

    - **graph_id**: 图谱ID
    - **source_id**: 源节点ID（必填）
    - **target_id**: 目标节点ID（必填）
    - **relationship_type**: 关系类型（必填）
    - **properties**: 关系属性（可选）

    返回添加的关系信息
    """
    edge = PrivateGraphService.add_edge(
        graph_id=graph_id,
        owner_id=str(current_user.id),
        source_id=request.source_id,
        target_id=request.target_id,
        relationship_type=request.relationship_type,
        properties=request.properties
    )

    if not edge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="添加关系失败：图谱不存在、无权限或节点不存在"
        )

    return edge


@router.delete("/{graph_id}/edge/{edge_id}")
def remove_edge(
    graph_id: str,
    edge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从私有图谱中删除关系

    - **graph_id**: 图谱ID
    - **edge_id**: 关系ID

    删除指定的关系
    """
    success = PrivateGraphService.remove_edge(graph_id, str(current_user.id), edge_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关系不存在或无权限删除"
        )

    return {"message": "关系已删除"}


@router.post("/{graph_id}/search", response_model=GraphSearchResult)
def search_graph(
    graph_id: str,
    request: GraphSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    在私有图谱中搜索

    - **graph_id**: 图谱ID
    - **query**: 搜索查询（必填）
    - **node_type**: 节点类型过滤（可选）
    - **limit**: 结果数量限制（1-100，默认: 20）

    返回匹配的节点和关系
    """
    result = PrivateGraphService.search_graph(
        graph_id=graph_id,
        owner_id=str(current_user.id),
        query=request.query,
        node_type=request.node_type,
        limit=request.limit
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图谱不存在或无权限访问: {graph_id}"
        )

    nodes, edges = result
    return GraphSearchResult(
        nodes=nodes,
        edges=edges,
        total=len(nodes)
    )
