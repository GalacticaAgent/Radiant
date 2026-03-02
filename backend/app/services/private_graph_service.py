"""
Private Graph Service - 私有知识图谱管理服务
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app.schemas.private_graph import (
    NodeResponse,
    EdgeResponse,
    PrivateGraphResponse,
    PrivateGraphDetailResponse
)


# 简单的内存存储（生产环境应使用Neo4j）
_private_graphs: Dict[str, dict] = {}
_nodes: Dict[str, dict] = {}  # graph_id -> {node_id -> node_data}
_edges: Dict[str, List[dict]] = {}  # graph_id -> [edge_data]


class PrivateGraphService:
    """私有知识图谱服务类"""

    @staticmethod
    def create_graph(owner_id: str, name: str, description: Optional[str] = None, is_public: bool = False) -> PrivateGraphResponse:
        """
        创建私有图谱

        Args:
            owner_id: 所有者ID
            name: 图谱名称
            description: 图谱描述
            is_public: 是否公开

        Returns:
            PrivateGraphResponse: 创建的图谱信息
        """
        graph_id = str(uuid.uuid4())
        now = datetime.utcnow()

        graph_data = {
            "id": graph_id,
            "owner_id": owner_id,
            "name": name,
            "description": description,
            "is_public": is_public,
            "created_at": now,
            "updated_at": now,
            "node_count": 0,
            "edge_count": 0
        }

        _private_graphs[graph_id] = graph_data
        _nodes[graph_id] = {}
        _edges[graph_id] = []

        return PrivateGraphResponse(**graph_data)

    @staticmethod
    def get_graph(graph_id: str, owner_id: str) -> Optional[PrivateGraphResponse]:
        """
        获取图谱信息（权限检查）

        Args:
            graph_id: 图谱ID
            owner_id: 请求者ID

        Returns:
            PrivateGraphResponse: 图谱信息，如果无权限则返回None
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data:
            return None

        # 权限检查：所有者或公开图谱
        if graph_data["owner_id"] != owner_id and not graph_data["is_public"]:
            return None

        return PrivateGraphResponse(**graph_data)

    @staticmethod
    def get_graph_detail(graph_id: str, owner_id: str) -> Optional[PrivateGraphDetailResponse]:
        """
        获取图谱详细信息（包含节点和边）

        Args:
            graph_id: 图谱ID
            owner_id: 请求者ID

        Returns:
            PrivateGraphDetailResponse: 图谱详细信息
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data:
            return None

        # 权限检查
        if graph_data["owner_id"] != owner_id and not graph_data["is_public"]:
            return None

        # 获取节点
        nodes = []
        graph_nodes = _nodes.get(graph_id, {})
        for node_id, node_data in graph_nodes.items():
            nodes.append(NodeResponse(
                id=node_id,
                type=node_data["type"],
                graph_id=graph_id,
                properties=node_data["properties"],
                created_at=node_data["created_at"]
            ))

        # 获取边
        edges = []
        graph_edges = _edges.get(graph_id, [])
        for edge_data in graph_edges:
            edges.append(EdgeResponse(
                id=edge_data["id"],
                source_id=edge_data["source_id"],
                target_id=edge_data["target_id"],
                relationship_type=edge_data["relationship_type"],
                graph_id=graph_id,
                properties=edge_data["properties"],
                created_at=edge_data["created_at"]
            ))

        return PrivateGraphDetailResponse(
            id=graph_data["id"],
            owner_id=graph_data["owner_id"],
            name=graph_data["name"],
            description=graph_data["description"],
            is_public=graph_data["is_public"],
            node_count=len(nodes),
            edge_count=len(edges),
            created_at=graph_data["created_at"],
            updated_at=graph_data["updated_at"],
            nodes=nodes,
            edges=edges
        )

    @staticmethod
    def update_graph(graph_id: str, owner_id: str, name: Optional[str] = None,
                     description: Optional[str] = None, is_public: Optional[bool] = None) -> Optional[PrivateGraphResponse]:
        """
        更新图谱信息

        Args:
            graph_id: 图谱ID
            owner_id: 所有者ID
            name: 新名称
            description: 新描述
            is_public: 新的公开状态

        Returns:
            PrivateGraphResponse: 更新后的图谱信息
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data or graph_data["owner_id"] != owner_id:
            return None

        if name is not None:
            graph_data["name"] = name
        if description is not None:
            graph_data["description"] = description
        if is_public is not None:
            graph_data["is_public"] = is_public

        graph_data["updated_at"] = datetime.utcnow()

        return PrivateGraphResponse(**graph_data)

    @staticmethod
    def delete_graph(graph_id: str, owner_id: str) -> bool:
        """
        删除图谱

        Args:
            graph_id: 图谱ID
            owner_id: 所有者ID

        Returns:
            bool: 是否删除成功
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data or graph_data["owner_id"] != owner_id:
            return False

        _private_graphs.pop(graph_id, None)
        _nodes.pop(graph_id, None)
        _edges.pop(graph_id, None)

        return True

    @staticmethod
    def add_node(graph_id: str, owner_id: str, node_id: str, node_type: str,
                 properties: Optional[dict] = None) -> Optional[NodeResponse]:
        """
        添加节点

        Args:
            graph_id: 图谱ID
            owner_id: 所有者ID
            node_id: 节点ID
            node_type: 节点类型
            properties: 节点属性

        Returns:
            NodeResponse: 添加的节点信息
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data or graph_data["owner_id"] != owner_id:
            return None

        graph_nodes = _nodes.get(graph_id, {})
        if node_id in graph_nodes:
            return None  # 节点已存在

        now = datetime.utcnow()
        node_data = {
            "id": node_id,
            "type": node_type,
            "properties": properties or {},
            "created_at": now
        }

        graph_nodes[node_id] = node_data
        graph_data["node_count"] = len(graph_nodes)
        graph_data["updated_at"] = now

        return NodeResponse(
            id=node_id,
            type=node_type,
            graph_id=graph_id,
            properties=properties or {},
            created_at=now
        )

    @staticmethod
    def remove_node(graph_id: str, owner_id: str, node_id: str) -> bool:
        """
        删除节点

        Args:
            graph_id: 图谱ID
            owner_id: 所有者ID
            node_id: 节点ID

        Returns:
            bool: 是否删除成功
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data or graph_data["owner_id"] != owner_id:
            return False

        graph_nodes = _nodes.get(graph_id, {})
        if node_id not in graph_nodes:
            return False

        # 删除节点
        graph_nodes.pop(node_id, None)

        # 删除相关的边
        graph_edges = _edges.get(graph_id, [])
        _edges[graph_id] = [
            e for e in graph_edges
            if e["source_id"] != node_id and e["target_id"] != node_id
        ]

        now = datetime.utcnow()
        graph_data["node_count"] = len(graph_nodes)
        graph_data["edge_count"] = len(_edges[graph_id])
        graph_data["updated_at"] = now

        return True

    @staticmethod
    def add_edge(graph_id: str, owner_id: str, source_id: str, target_id: str,
                 relationship_type: str, properties: Optional[dict] = None) -> Optional[EdgeResponse]:
        """
        添加关系（边）

        Args:
            graph_id: 图谱ID
            owner_id: 所有者ID
            source_id: 源节点ID
            target_id: 目标节点ID
            relationship_type: 关系类型
            properties: 关系属性

        Returns:
            EdgeResponse: 添加的关系信息
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data or graph_data["owner_id"] != owner_id:
            return None

        graph_nodes = _nodes.get(graph_id, {})
        if source_id not in graph_nodes or target_id not in graph_nodes:
            return None  # 节点不存在

        edge_id = str(uuid.uuid4())
        now = datetime.utcnow()
        edge_data = {
            "id": edge_id,
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "properties": properties or {},
            "created_at": now
        }

        graph_edges = _edges.get(graph_id, [])
        graph_edges.append(edge_data)
        graph_data["edge_count"] = len(graph_edges)
        graph_data["updated_at"] = now

        return EdgeResponse(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            graph_id=graph_id,
            properties=properties or {},
            created_at=now
        )

    @staticmethod
    def remove_edge(graph_id: str, owner_id: str, edge_id: str) -> bool:
        """
        删除关系

        Args:
            graph_id: 图谱ID
            owner_id: 所有者ID
            edge_id: 关系ID

        Returns:
            bool: 是否删除成功
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data or graph_data["owner_id"] != owner_id:
            return False

        graph_edges = _edges.get(graph_id, [])
        original_count = len(graph_edges)

        _edges[graph_id] = [e for e in graph_edges if e["id"] != edge_id]

        if len(_edges[graph_id]) < original_count:
            graph_data["edge_count"] = len(_edges[graph_id])
            graph_data["updated_at"] = datetime.utcnow()
            return True

        return False

    @staticmethod
    def list_user_graphs(owner_id: str) -> List[PrivateGraphResponse]:
        """
        列出用户的所有图谱

        Args:
            owner_id: 所有者ID

        Returns:
            List[PrivateGraphResponse]: 用户的图谱列表
        """
        graphs = []
        for graph_id, graph_data in _private_graphs.items():
            if graph_data["owner_id"] == owner_id:
                graphs.append(PrivateGraphResponse(**graph_data))

        return sorted(graphs, key=lambda x: x.created_at, reverse=True)

    @staticmethod
    def search_graph(graph_id: str, owner_id: str, query: str, node_type: Optional[str] = None,
                     limit: int = 20) -> Optional[Tuple[List[NodeResponse], List[EdgeResponse]]]:
        """
        在图谱中搜索

        Args:
            graph_id: 图谱ID
            owner_id: 请求者ID
            query: 搜索查询
            node_type: 节点类型过滤
            limit: 结果数量限制

        Returns:
            Tuple[List[NodeResponse], List[EdgeResponse]]: 匹配的节点和关系
        """
        graph_data = _private_graphs.get(graph_id)
        if not graph_data:
            return None

        # 权限检查
        if graph_data["owner_id"] != owner_id and not graph_data["is_public"]:
            return None

        # 搜索节点
        matching_nodes = []
        graph_nodes = _nodes.get(graph_id, {})
        query_lower = query.lower()

        for node_id, node_data in graph_nodes.items():
            # 检查节点ID、类型和属性
            if (query_lower in node_id.lower() or
                query_lower in node_data["type"].lower() or
                any(query_lower in str(v).lower() for v in node_data["properties"].values())):

                if node_type is None or node_data["type"] == node_type:
                    matching_nodes.append(NodeResponse(
                        id=node_id,
                        type=node_data["type"],
                        graph_id=graph_id,
                        properties=node_data["properties"],
                        created_at=node_data["created_at"]
                    ))

                if len(matching_nodes) >= limit:
                    break

        # 获取相关的关系
        matching_node_ids = {node.id for node in matching_nodes}
        matching_edges = []
        graph_edges = _edges.get(graph_id, [])

        for edge_data in graph_edges:
            if (edge_data["source_id"] in matching_node_ids or
                edge_data["target_id"] in matching_node_ids):
                matching_edges.append(EdgeResponse(
                    id=edge_data["id"],
                    source_id=edge_data["source_id"],
                    target_id=edge_data["target_id"],
                    relationship_type=edge_data["relationship_type"],
                    graph_id=graph_id,
                    properties=edge_data["properties"],
                    created_at=edge_data["created_at"]
                ))

        return matching_nodes, matching_edges
