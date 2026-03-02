"""
Celery 爬虫任务
定时和按需爬取学术数据
"""

from celery import shared_task
from app.crawlers.arxiv_crawler import ArxivCrawler, get_hot_papers
from app.crawlers.semantic_scholar_crawler import SemanticScholarCrawler
from app.crawlers.github_crawler import GitHubCrawler
from app.services.graph_builder_service import GraphBuilderService
from app.db.neo4j import get_neo4j
from app.core.config import settings
from loguru import logger
from typing import List, Dict, Any


@shared_task(name="crawl_hot_papers")
def crawl_hot_papers_task(max_results: int = 50) -> Dict[str, Any]:
    """
    定时任务：爬取热门论文

    Args:
        max_results: 最大爬取数量

    Returns:
        Dict: 爬取结果统计
    """
    try:
        logger.info(f"开始定时爬取热门论文，目标数量: {max_results}")

        # 1. 爬取 arXiv 论文
        arxiv_crawler = ArxivCrawler(max_results=max_results)
        papers = arxiv_crawler.crawl_hot_papers()

        logger.info(f"arXiv 爬取完成，获得 {len(papers)} 篇论文")

        # 2. 写入知识图谱
        neo4j_conn = get_neo4j()
        graph_builder = GraphBuilderService(neo4j_conn)

        stats = graph_builder.batch_add_papers(papers)

        logger.info(f"定时爬取任务完成: {stats}")

        return {
            "status": "success",
            "papers_crawled": len(papers),
            "papers_added": stats["success"],
            "papers_failed": stats["failed"]
        }

    except Exception as e:
        logger.error(f"定时爬取任务失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@shared_task(name="crawl_papers_by_query")
def crawl_papers_by_query_task(query: str, max_results: int = 20) -> Dict[str, Any]:
    """
    按需任务：根据查询爬取论文

    Args:
        query: 搜索查询
        max_results: 最大结果数

    Returns:
        Dict: 爬取结果
    """
    try:
        logger.info(f"按需爬取论文: query='{query}', max={max_results}")

        # 爬取论文
        arxiv_crawler = ArxivCrawler(max_results=max_results)
        papers = arxiv_crawler.search_papers(query)

        # 写入知识图谱
        neo4j_conn = get_neo4j()
        graph_builder = GraphBuilderService(neo4j_conn)
        stats = graph_builder.batch_add_papers(papers)

        logger.info(f"按需爬取完成: {stats}")

        return {
            "status": "success",
            "query": query,
            "papers_found": len(papers),
            "papers_added": stats["success"],
            "paper_ids": stats["paper_ids"]
        }

    except Exception as e:
        logger.error(f"按需爬取失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@shared_task(name="enrich_papers_with_semantic_scholar")
def enrich_papers_task(arxiv_ids: List[str], max_papers: int = 20) -> Dict[str, Any]:
    """
    补充论文信息（使用 Semantic Scholar）

    Args:
        arxiv_ids: arXiv ID 列表
        max_papers: 最大处理数量

    Returns:
        Dict: 补充结果
    """
    try:
        logger.info(f"开始补充 {len(arxiv_ids)} 篇论文的引用信息...")

        # 使用 Semantic Scholar 补充信息
        ss_crawler = SemanticScholarCrawler()
        enriched = ss_crawler.batch_enrich_papers(arxiv_ids, max_papers)

        logger.info(f"补充完成，成功 {len(enriched)} 篇")

        # TODO: 将引用关系写入知识图谱

        return {
            "status": "success",
            "total": len(arxiv_ids),
            "enriched": len(enriched)
        }

    except Exception as e:
        logger.error(f"补充论文信息失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@shared_task(name="crawl_github_implementations")
def crawl_github_implementations_task(
    paper_title: str,
    arxiv_id: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    爬取论文的 GitHub 实现

    Args:
        paper_title: 论文标题
        arxiv_id: arXiv ID
        max_results: 最大结果数

    Returns:
        Dict: 爬取结果
    """
    try:
        logger.info(f"搜索论文实现: {paper_title}")

        # 搜索 GitHub 仓库
        github_crawler = GitHubCrawler(token=settings.GITHUB_TOKEN)
        repos = github_crawler.search_paper_implementations(
            paper_title,
            arxiv_id,
            max_results
        )

        logger.info(f"找到 {len(repos)} 个相关仓库")

        # 写入知识图谱
        neo4j_conn = get_neo4j()
        graph_builder = GraphBuilderService(neo4j_conn)

        repo_ids = []
        for repo in repos:
            try:
                # 添加代码节点
                code_id = graph_builder.add_code_project(repo)
                repo_ids.append(code_id)

                # 关联到论文
                paper_id = f"arxiv-{arxiv_id}"
                graph_builder.link_code_to_paper(code_id, paper_id)

            except Exception as e:
                logger.error(f"添加代码项目失败: {str(e)}")

        return {
            "status": "success",
            "repos_found": len(repos),
            "repos_added": len(repo_ids),
            "repo_ids": repo_ids
        }

    except Exception as e:
        logger.error(f"爬取 GitHub 实现失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@shared_task(name="update_graph_stats")
def update_graph_stats_task() -> Dict[str, Any]:
    """
    更新知识图谱统计信息

    Returns:
        Dict: 统计信息
    """
    try:
        neo4j_conn = get_neo4j()
        graph_builder = GraphBuilderService(neo4j_conn)

        stats = graph_builder.get_graph_stats()

        logger.info(f"知识图谱统计: {stats}")

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }
