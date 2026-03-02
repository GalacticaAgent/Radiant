"""
知识图谱服务
提供与 Neo4j 的交互和图谱查询功能
"""

from typing import List, Dict, Any, Optional
from app.db.neo4j import Neo4jConnection, get_neo4j
import logging

logger = logging.getLogger(__name__)


class GraphService:
    """知识图谱服务类"""

    def __init__(self, neo4j_conn: Neo4jConnection):
        """
        初始化图谱服务

        Args:
            neo4j_conn: Neo4j 连接实例
        """
        self.neo4j = neo4j_conn

    def search_nodes(
        self,
        query: str,
        node_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        全文搜索节点

        Args:
            query: 搜索关键词
            node_type: 节点类型（可选）
            limit: 返回结果数量限制

        Returns:
            List[Dict]: 搜索结果
        """
        if node_type:
            cypher = f"""
            MATCH (n:{node_type})
            WHERE n.title CONTAINS $query OR n.name CONTAINS $query
            RETURN n LIMIT $limit
            """
        else:
            cypher = """
            MATCH (n)
            WHERE n.title CONTAINS $query OR n.name CONTAINS $query
            RETURN n LIMIT $limit
            """

        try:
            results = self.neo4j.execute_query(cypher, {"query": query, "limit": limit})
            return results
        except Exception as e:
            logger.error(f"搜索节点失败: {e}")
            return []

    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取节点详细信息

        Args:
            node_id: 节点ID

        Returns:
            Optional[Dict]: 节点信息
        """
        cypher = """
        MATCH (n {id: $id})
        OPTIONAL MATCH (n)-[rel]-(related)
        RETURN n, collect({type: type(rel), node: related}) as relationships
        """

        try:
            results = self.neo4j.execute_query(cypher, {"id": node_id})
            return results[0] if results else None
        except Exception as e:
            logger.error(f"获取节点详情失败: {e}")
            return None

    def get_subgraph(
        self,
        query: str,
        depth: int = 2,
        limit: int = 100,
        node_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提取子图

        Args:
            query: 搜索关键词
            depth: 图谱深度
            limit: 节点数量限制
            node_type: 节点类型过滤（可选）

        Returns:
            Dict: 包含 nodes 和 edges 的子图数据
        """
        # 搜索起始节点
        start_cypher = f"""
        MATCH (n{":" + node_type if node_type else ""})
        WHERE n.title CONTAINS $query OR n.name CONTAINS $query OR n.abstract CONTAINS $query
        RETURN n LIMIT 1
        """

        try:
            start_nodes = self.neo4j.execute_query(start_cypher, {"query": query})

            if not start_nodes:
                return {"nodes": [], "edges": []}

            start_node_id = start_nodes[0].get("n", {}).get("id")

            # 获取子图
            subgraph_cypher = f"""
            MATCH (start {{id: $start_id}})
            MATCH path = (start)-[*1..{depth}]-(node)
            WITH nodes(path) as nodes, relationships(path) as rels
            UNWIND nodes as n
            WITH DISTINCT n, rels
            RETURN n, rels
            LIMIT $limit
            """

            results = self.neo4j.execute_query(
                subgraph_cypher,
                {"start_id": start_node_id, "limit": limit}
            )

            # 处理结果，构建 nodes 和 edges
            nodes = []
            edges = []
            node_ids = set()

            for result in results:
                node_data = result.get("n", {})
                if node_data:
                    node_id = node_data.get("id")
                    if node_id and node_id not in node_ids:
                        node_ids.add(node_id)
                        nodes.append({
                            "id": node_id,
                            "label": node_data.get("title") or node_data.get("name", node_id),
                            "type": self._get_node_type(node_data),
                            "properties": node_data
                        })

                # 处理关系
                rels = result.get("rels", [])
                if rels:
                    for rel in rels:
                        rel_type = rel.get("type")
                        start = rel.get("start")
                        end = rel.get("end")
                        if start and end and rel_type:
                            edges.append({
                                "source": start,
                                "target": end,
                                "type": rel_type
                            })

            return {"nodes": nodes[:limit], "edges": edges}

        except Exception as e:
            logger.error(f"提取子图失败: {e}")
            return {"nodes": [], "edges": []}

    def add_paper(self, paper_data: Dict[str, Any]) -> bool:
        """
        添加论文节点

        Args:
            paper_data: 论文数据

        Returns:
            bool: 是否成功
        """
        cypher = """
        MERGE (p:Paper {id: $id})
        SET p.title = $title,
            p.abstract = $abstract,
            p.year = $year,
            p.venue = $venue,
            p.arxiv_id = $arxiv_id,
            p.doi = $doi,
            p.citations = $citations,
            p.keywords = $keywords,
            p.created_at = datetime()
        RETURN p
        """

        try:
            self.neo4j.execute_query(cypher, paper_data)
            return True
        except Exception as e:
            logger.error(f"添加论文失败: {e}")
            return False

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加关系

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relationship_type: 关系类型
            properties: 关系属性（可选）

        Returns:
            bool: 是否成功
        """
        cypher = f"""
        MATCH (a {{id: $source_id}})
        MATCH (b {{id: $target_id}})
        CREATE (a)-[r:{relationship_type}]->(b)
        SET r += $properties
        RETURN r
        """

        try:
            self.neo4j.execute_query(
                cypher,
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "properties": properties or {}
                }
            )
            return True
        except Exception as e:
            logger.error(f"添加关系失败: {e}")
            return False

    def get_related_papers(self, paper_id: str, depth: int = 2, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取相关论文

        Args:
            paper_id: 论文ID
            depth: 搜索深度
            limit: 结果限制

        Returns:
            List[Dict]: 相关论文列表
        """
        cypher = f"""
        MATCH (p:Paper {{id: $paper_id}})
        MATCH (p)-[*1..{depth}]-(related:Paper)
        WHERE related.id <> p.id
        RETURN DISTINCT related
        ORDER BY related.citations DESC
        LIMIT $limit
        """

        try:
            results = self.neo4j.execute_query(
                cypher,
                {"paper_id": paper_id, "limit": limit}
            )
            return [result.get("related", {}) for result in results if result.get("related")]
        except Exception as e:
            logger.error(f"获取相关论文失败: {e}")
            return []

    def get_researcher_papers(self, researcher_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取研究者发表的论文

        Args:
            researcher_id: 研究者ID
            limit: 结果限制

        Returns:
            List[Dict]: 论文列表
        """
        cypher = """
        MATCH (p:Person {id: $researcher_id})-[:AUTHORED]->(paper:Paper)
        RETURN paper
        ORDER BY paper.year DESC
        LIMIT $limit
        """

        try:
            results = self.neo4j.execute_query(
                cypher,
                {"researcher_id": researcher_id, "limit": limit}
            )
            return [result.get("paper", {}) for result in results if result.get("paper")]
        except Exception as e:
            logger.error(f"获取研究者论文失败: {e}")
            return []

    @staticmethod
    def _get_node_type(node_data: Dict[str, Any]) -> str:
        """
        推断节点类型

        Args:
            node_data: 节点数据

        Returns:
            str: 节点类型
        """
        # 这是一个简化的推断方法，实际应该从 Neo4j 标签获取
        if "title" in node_data:
            return "Paper"
        elif "affiliation" in node_data:
            return "Person"
        elif "website" in node_data:
            return "Organization"
        elif "github_url" in node_data:
            return "Code"
        return "Unknown"


def get_graph_service(neo4j_conn: Neo4jConnection = None) -> GraphService:
    """
    获取图谱服务的依赖函数

    Args:
        neo4j_conn: Neo4j 连接（可选，默认使用全局连接）

    Returns:
        GraphService: 图谱服务实例
    """
    if neo4j_conn is None:
        neo4j_conn = get_neo4j()
    return GraphService(neo4j_conn)
