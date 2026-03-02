"""
arXiv 论文爬虫
使用官方 arxiv 库抓取论文元数据
"""

import arxiv
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class ArxivCrawler:
    """arXiv 论文爬虫类"""

    def __init__(self, max_results: int = 50, delay: int = 1):
        """
        初始化 arXiv 爬虫

        Args:
            max_results: 最大返回结果数
            delay: 请求延迟（秒）
        """
        self.max_results = max_results
        self.delay = delay

    def search_papers(
        self,
        query: str,
        max_results: Optional[int] = None,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending
    ) -> List[Dict[str, Any]]:
        """
        搜索论文

        Args:
            query: 搜索查询（支持arXiv查询语法）
            max_results: 最大结果数
            sort_by: 排序依据
            sort_order: 排序顺序

        Returns:
            List[Dict]: 论文列表
        """
        max_results = max_results or self.max_results
        papers = []

        try:
            logger.info(f"开始搜索 arXiv 论文: query='{query}', max_results={max_results}")

            # 创建搜索客户端
            client = arxiv.Client(
                page_size=100,
                delay_seconds=self.delay,
                num_retries=3
            )

            # 执行搜索
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # 处理结果
            for result in client.results(search):
                paper_data = self._parse_paper(result)
                papers.append(paper_data)

                if len(papers) % 10 == 0:
                    logger.info(f"已爬取 {len(papers)} 篇论文...")

            logger.info(f"arXiv 爬取完成，共获取 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            logger.error(f"arXiv 搜索失败: {str(e)}")
            return papers

    def get_papers_by_category(
        self,
        category: str,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        按分类获取论文

        Args:
            category: arXiv 分类代码 (如 cs.AI, cs.CL, cs.LG)
            max_results: 最大结果数

        Returns:
            List[Dict]: 论文列表
        """
        query = f"cat:{category}"
        return self.search_papers(query, max_results)

    def get_recent_papers(
        self,
        days: int = 7,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取最近N天的论文

        Args:
            days: 天数
            max_results: 最大结果数

        Returns:
            List[Dict]: 论文列表
        """
        # arXiv 默认按提交日期降序排序，直接获取最新的
        query = "all:*"  # 所有论文
        return self.search_papers(query, max_results)

    def get_papers_by_authors(
        self,
        author_names: List[str],
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        按作者名称搜索论文

        Args:
            author_names: 作者名称列表
            max_results: 最大结果数

        Returns:
            List[Dict]: 论文列表
        """
        # 构建作者查询
        author_queries = [f'au:"{name}"' for name in author_names]
        query = " OR ".join(author_queries)

        return self.search_papers(query, max_results)

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        通过 arXiv ID 获取论文详情

        Args:
            arxiv_id: arXiv ID (如 2301.00001)

        Returns:
            Dict: 论文信息，失败返回 None
        """
        try:
            logger.info(f"获取 arXiv 论文: {arxiv_id}")

            client = arxiv.Client()
            search = arxiv.Search(id_list=[arxiv_id])

            result = next(client.results(search))
            return self._parse_paper(result)

        except Exception as e:
            logger.error(f"获取 arXiv 论文失败 {arxiv_id}: {str(e)}")
            return None

    def _parse_paper(self, result: arxiv.Result) -> Dict[str, Any]:
        """
        解析论文结果

        Args:
            result: arxiv.Result 对象

        Returns:
            Dict: 标准化的论文数据
        """
        # 提取作者信息
        authors = [
            {
                "name": author.name,
                "affiliation": getattr(author, 'affiliation', None)
            }
            for author in result.authors
        ]

        # 提取分类
        categories = [cat for cat in result.categories]

        # 构建论文数据
        paper_data = {
            "id": f"arxiv-{result.entry_id.split('/')[-1]}",
            "arxiv_id": result.entry_id.split('/')[-1],
            "title": result.title,
            "abstract": result.summary,
            "authors": authors,
            "categories": categories,
            "primary_category": result.primary_category,
            "published": result.published.isoformat() if result.published else None,
            "updated": result.updated.isoformat() if result.updated else None,
            "pdf_url": result.pdf_url,
            "entry_url": result.entry_id,
            "doi": result.doi,
            "journal_ref": result.journal_ref,
            "comment": result.comment,
            "source": "arxiv",
            "crawled_at": datetime.utcnow().isoformat()
        }

        return paper_data

    def get_popular_categories(self) -> List[str]:
        """
        获取热门分类列表

        Returns:
            List[str]: 分类代码列表
        """
        return [
            "cs.AI",  # Artificial Intelligence
            "cs.CL",  # Computation and Language (NLP)
            "cs.CV",  # Computer Vision
            "cs.LG",  # Machine Learning
            "cs.NE",  # Neural and Evolutionary Computing
            "stat.ML",  # Machine Learning (Statistics)
            "cs.IR",  # Information Retrieval
            "cs.RO",  # Robotics
        ]

    def crawl_hot_papers(self, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        爬取热门分类的最新论文

        Args:
            categories: 分类列表，默认使用热门分类

        Returns:
            List[Dict]: 论文列表
        """
        categories = categories or self.get_popular_categories()
        all_papers = []

        papers_per_category = max(5, self.max_results // len(categories))

        for category in categories:
            logger.info(f"爬取分类: {category}")
            papers = self.get_papers_by_category(category, papers_per_category)
            all_papers.extend(papers)

            if len(all_papers) >= self.max_results:
                break

        # 去重（基于arxiv_id）
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            arxiv_id = paper.get('arxiv_id')
            if arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                unique_papers.append(paper)

        logger.info(f"热门论文爬取完成，共 {len(unique_papers)} 篇（去重后）")
        return unique_papers[:self.max_results]


# 便捷函数
def search_arxiv(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    快捷搜索函数

    Args:
        query: 搜索查询
        max_results: 最大结果数

    Returns:
        List[Dict]: 论文列表
    """
    crawler = ArxivCrawler(max_results=max_results)
    return crawler.search_papers(query)


def get_hot_papers(max_results: int = 50) -> List[Dict[str, Any]]:
    """
    获取热门论文

    Args:
        max_results: 最大结果数

    Returns:
        List[Dict]: 论文列表
    """
    crawler = ArxivCrawler(max_results=max_results)
    return crawler.crawl_hot_papers()
