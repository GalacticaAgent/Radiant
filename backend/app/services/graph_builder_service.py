"""
知识图谱构建服务
将爬取的数据写入 Neo4j 知识图谱
"""

from typing import List, Dict, Any, Optional
from app.db.neo4j import Neo4jConnection
from loguru import logger
from datetime import datetime


class GraphBuilderService:
    """知识图谱构建服务"""

    def __init__(self, neo4j_conn: Neo4jConnection):
        """
        初始化服务

        Args:
            neo4j_conn: Neo4j 连接实例
        """
        self.neo4j = neo4j_conn

    def add_paper(self, paper_data: Dict[str, Any]) -> str:
        """
        添加论文节点到知识图谱

        Args:
            paper_data: 论文数据

        Returns:
            str: 论文节点ID
        """
        try:
            # 创建论文节点
            query = """
            MERGE (p:Paper {id: $id})
            SET p.arxiv_id = $arxiv_id,
                p.title = $title,
                p.abstract = $abstract,
                p.categories = $categories,
                p.primary_category = $primary_category,
                p.published = $published,
                p.updated = $updated,
                p.pdf_url = $pdf_url,
                p.entry_url = $entry_url,
                p.doi = $doi,
                p.journal_ref = $journal_ref,
                p.comment = $comment,
                p.source = $source,
                p.crawled_at = datetime($crawled_at),
                p.updated_at = datetime()
            RETURN p.id as paper_id
            """

            params = {
                "id": paper_data.get("id"),
                "arxiv_id": paper_data.get("arxiv_id"),
                "title": paper_data.get("title"),
                "abstract": paper_data.get("abstract", "")[:1000],  # 限制长度
                "categories": paper_data.get("categories", []),
                "primary_category": paper_data.get("primary_category"),
                "published": paper_data.get("published"),
                "updated": paper_data.get("updated"),
                "pdf_url": paper_data.get("pdf_url"),
                "entry_url": paper_data.get("entry_url"),
                "doi": paper_data.get("doi"),
                "journal_ref": paper_data.get("journal_ref"),
                "comment": paper_data.get("comment"),
                "source": paper_data.get("source", "arxiv"),
                "crawled_at": paper_data.get("crawled_at", datetime.utcnow().isoformat())
            }

            result = self.neo4j.execute_query(query, params)
            paper_id = result[0]["paper_id"] if result else paper_data.get("id")

            logger.info(f"论文节点已添加: {paper_id}")
            return paper_id

        except Exception as e:
            logger.error(f"添加论文节点失败: {str(e)}")
            raise

    def add_authors(self, paper_id: str, authors: List[Dict[str, Any]]) -> List[str]:
        """
        添加作者节点并关联到论文

        Args:
            paper_id: 论文ID
            authors: 作者列表

        Returns:
            List[str]: 作者ID列表
        """
        author_ids = []

        try:
            for idx, author in enumerate(authors):
                author_name = author.get("name")
                if not author_name:
                    continue

                # 生成作者ID（使用名字的标准化形式）
                author_id = f"person-{author_name.lower().replace(' ', '-')}"

                # 创建作者节点
                query = """
                MERGE (a:Person {id: $id})
                SET a.name = $name,
                    a.updated_at = datetime()
                WITH a
                MATCH (p:Paper {id: $paper_id})
                MERGE (a)-[r:AUTHORED]->(p)
                SET r.position = $position,
                    r.created_at = datetime()
                RETURN a.id as author_id
                """

                params = {
                    "id": author_id,
                    "name": author_name,
                    "paper_id": paper_id,
                    "position": idx + 1
                }

                result = self.neo4j.execute_query(query, params)
                if result:
                    author_ids.append(result[0]["author_id"])

            logger.info(f"添加 {len(author_ids)} 个作者到论文 {paper_id}")
            return author_ids

        except Exception as e:
            logger.error(f"添加作者失败: {str(e)}")
            return author_ids

    def add_paper_with_authors(self, paper_data: Dict[str, Any]) -> str:
        """
        添加论文及其作者到知识图谱

        Args:
            paper_data: 论文数据（包含authors字段）

        Returns:
            str: 论文ID
        """
        # 添加论文节点
        paper_id = self.add_paper(paper_data)

        # 添加作者及关系
        authors = paper_data.get("authors", [])
        if authors:
            self.add_authors(paper_id, authors)

        return paper_id

    def batch_add_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量添加论文到知识图谱

        Args:
            papers: 论文列表

        Returns:
            Dict: 添加统计信息
        """
        stats = {
            "total": len(papers),
            "success": 0,
            "failed": 0,
            "paper_ids": []
        }

        logger.info(f"开始批量添加 {len(papers)} 篇论文到知识图谱...")

        for idx, paper in enumerate(papers):
            try:
                paper_id = self.add_paper_with_authors(paper)
                stats["success"] += 1
                stats["paper_ids"].append(paper_id)

                if (idx + 1) % 10 == 0:
                    logger.info(f"进度: {idx + 1}/{len(papers)}")

            except Exception as e:
                stats["failed"] += 1
                logger.error(f"添加论文失败: {paper.get('title', 'Unknown')}, 错误: {str(e)}")

        logger.info(f"批量添加完成: 成功 {stats['success']}, 失败 {stats['failed']}")
        return stats

    def add_organization(self, org_data: Dict[str, Any]) -> str:
        """
        添加机构节点

        Args:
            org_data: 机构数据

        Returns:
            str: 机构ID
        """
        try:
            query = """
            MERGE (o:Organization {id: $id})
            SET o.name = $name,
                o.type = $type,
                o.country = $country,
                o.website = $website,
                o.updated_at = datetime()
            RETURN o.id as org_id
            """

            params = {
                "id": org_data.get("id"),
                "name": org_data.get("name"),
                "type": org_data.get("type", "unknown"),
                "country": org_data.get("country"),
                "website": org_data.get("website")
            }

            result = self.neo4j.execute_query(query, params)
            org_id = result[0]["org_id"] if result else org_data.get("id")

            logger.info(f"机构节点已添加: {org_id}")
            return org_id

        except Exception as e:
            logger.error(f"添加机构节点失败: {str(e)}")
            raise

    def add_code_project(self, code_data: Dict[str, Any]) -> str:
        """
        添加代码项目节点

        Args:
            code_data: 代码项目数据

        Returns:
            str: 项目ID
        """
        try:
            query = """
            MERGE (c:Code {id: $id})
            SET c.name = $name,
                c.description = $description,
                c.github_url = $github_url,
                c.language = $language,
                c.stars = $stars,
                c.forks = $forks,
                c.topics = $topics,
                c.updated_at = datetime()
            RETURN c.id as code_id
            """

            params = {
                "id": code_data.get("id"),
                "name": code_data.get("name"),
                "description": code_data.get("description"),
                "github_url": code_data.get("github_url"),
                "language": code_data.get("language"),
                "stars": code_data.get("stars", 0),
                "forks": code_data.get("forks", 0),
                "topics": code_data.get("topics", [])
            }

            result = self.neo4j.execute_query(query, params)
            code_id = result[0]["code_id"] if result else code_data.get("id")

            logger.info(f"代码项目节点已添加: {code_id}")
            return code_id

        except Exception as e:
            logger.error(f"添加代码项目失败: {str(e)}")
            raise

    def link_code_to_paper(self, code_id: str, paper_id: str) -> bool:
        """
        建立代码-论文关联关系

        Args:
            code_id: 代码项目ID
            paper_id: 论文ID

        Returns:
            bool: 是否成功
        """
        try:
            query = """
            MATCH (c:Code {id: $code_id})
            MATCH (p:Paper {id: $paper_id})
            MERGE (c)-[r:IMPLEMENTS]->(p)
            SET r.created_at = datetime()
            RETURN r
            """

            params = {
                "code_id": code_id,
                "paper_id": paper_id
            }

            self.neo4j.execute_query(query, params)
            logger.info(f"已建立代码-论文关联: {code_id} -> {paper_id}")
            return True

        except Exception as e:
            logger.error(f"建立代码-论文关联失败: {str(e)}")
            return False

    def get_graph_stats(self) -> Dict[str, int]:
        """
        获取知识图谱统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            # 统计各类型节点数量
            query = """
            MATCH (n)
            WITH labels(n)[0] as label, count(n) as count
            RETURN label, count
            """

            result = self.neo4j.execute_query(query)
            node_counts = {record["label"]: record["count"] for record in result}

            # 统计关系数量
            query = """
            MATCH ()-[r]->()
            WITH type(r) as rel_type, count(r) as count
            RETURN rel_type, count
            """

            result = self.neo4j.execute_query(query)
            rel_counts = {record["rel_type"]: record["count"] for record in result}

            stats = {
                "nodes": node_counts,
                "relationships": rel_counts,
                "total_nodes": sum(node_counts.values()),
                "total_relationships": sum(rel_counts.values())
            }

            return stats

        except Exception as e:
            logger.error(f"获取图谱统计失败: {str(e)}")
            return {}
