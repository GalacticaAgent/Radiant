"""
Neo4j 图数据库连接
"""

from neo4j import GraphDatabase, Session as Neo4jSession
from typing import Any, Dict, List, Optional
from app.core.config import settings


class Neo4jConnection:
    """Neo4j 数据库连接类"""

    def __init__(self, uri: str, user: str, password: str):
        """
        初始化 Neo4j 连接

        Args:
            uri: Neo4j 连接 URI
            user: 用户名
            password: 密码
        """
        self._driver = GraphDatabase.driver(uri, auth=(user, password), connection_timeout=5)

    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行 Cypher 查询

        Args:
            query: Cypher 查询语句
            parameters: 查询参数

        Returns:
            List[Dict]: 查询结果列表
        """
        with self._driver.session() as session:
            result = session.run(query, parameters or {}, timeout=5)
            return [record.data() for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        执行写入操作

        Args:
            query: Cypher 写入语句
            parameters: 查询参数
        """
        with self._driver.session() as session:
            session.write_transaction(lambda tx: tx.run(query, parameters or {}, timeout=5))

    def verify_connectivity(self) -> bool:
        """
        验证连接是否正常

        Returns:
            bool: 连接是否正常
        """
        try:
            with self._driver.session() as session:
                result = session.run("RETURN 1 as num")
                return result.single()["num"] == 1
        except Exception:
            return False


# 创建全局 Neo4j 连接实例
neo4j_conn = Neo4jConnection(
    uri=settings.NEO4J_URI,
    user=settings.NEO4J_USER,
    password=settings.NEO4J_PASSWORD
)


def get_neo4j() -> Neo4jConnection:
    """
    获取 Neo4j 连接的依赖函数
    用于 FastAPI 的依赖注入

    Returns:
        Neo4jConnection: Neo4j 连接实例
    """
    return neo4j_conn
