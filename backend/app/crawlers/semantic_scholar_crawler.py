"""
Semantic Scholar 爬虫
使用免费 API 补充论文引用关系和作者信息
注意：免费版限制 100 次/5分钟
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
import time


class SemanticScholarCrawler:
    """Semantic Scholar 爬虫类"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        delay: float = 3.0,
        max_retries: int = 5,
        max_backoff_seconds: int = 60,
        block_on_rate_limit: bool = True,
    ):
        """
        初始化爬虫

        Args:
            api_key: API 密钥（可选，免费版不需要）
            delay: 请求延迟（免费版推荐3秒以上）
            max_retries: 最大重试次数（后台任务可提高成功率）
            max_backoff_seconds: 最大退避秒数
            block_on_rate_limit: 429 时是否等待重试（在线接口建议 False）
        """
        self.api_key = api_key
        self.delay = delay
        self.last_request_time = 0
        self.max_retries = max_retries
        self.max_backoff_seconds = max_backoff_seconds
        self.block_on_rate_limit = block_on_rate_limit

        # 设置请求头
        self.headers = {
            "User-Agent": "Radiant-Academic-Assistant/1.0"
        }
        if api_key:
            self.headers["x-api-key"] = api_key

    def _wait_for_rate_limit(self):
        """等待以遵守速率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

    def _request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[httpx.Response]:
        attempt = 0
        backoff = 2.0
        last_status = None
        while attempt <= self.max_retries:
            try:
                self._wait_for_rate_limit()
                with httpx.Client(timeout=30.0) as client:
                    resp = client.get(url, params=params, headers=self.headers)
                last_status = resp.status_code
                if resp.status_code == 200:
                    return resp
                if resp.status_code == 404:
                    return resp
                if resp.status_code == 429:
                    if not self.block_on_rate_limit:
                        return resp
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_s = float(retry_after)
                        except Exception:
                            wait_s = backoff
                    else:
                        wait_s = backoff
                    wait_s = min(float(wait_s), float(self.max_backoff_seconds))
                    logger.warning(f"Semantic Scholar 429, backoff {wait_s:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_s)
                    backoff = min(backoff * 2.0, float(self.max_backoff_seconds))
                    attempt += 1
                    continue
                if 500 <= resp.status_code < 600:
                    wait_s = min(backoff, float(self.max_backoff_seconds))
                    logger.warning(f"Semantic Scholar {resp.status_code}, backoff {wait_s:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_s)
                    backoff = min(backoff * 2.0, float(self.max_backoff_seconds))
                    attempt += 1
                    continue
                return resp
            except Exception as e:
                wait_s = min(backoff, float(self.max_backoff_seconds))
                logger.warning(f"Semantic Scholar request error: {str(e)} (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait_s)
                backoff = min(backoff * 2.0, float(self.max_backoff_seconds))
                attempt += 1
        logger.warning(f"Semantic Scholar request failed after retries, last_status={last_status}")
        return None

    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/paper/{paper_id}"
            fields = [
                "paperId",
                "title",
                "abstract",
                "year",
                "venue",
                "citationCount",
                "referenceCount",
                "influentialCitationCount",
                "authors",
                "url",
                "externalIds",
                "fieldsOfStudy",
                "publicationDate",
            ]
            params = {"fields": ",".join(fields)}
            resp = self._request(url, params=params)
            if not resp:
                return None
            if resp.status_code == 200:
                return self._parse_paper(resp.json())
            return None
        except Exception as e:
            logger.error(f"获取论文详情失败: {str(e)}")
            return None

    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        通过 arXiv ID 获取论文详情

        Args:
            arxiv_id: arXiv ID (如 2301.00001)

        Returns:
            Dict: 论文信息，失败返回 None
        """
        try:
            # 构建请求URL
            url = f"{self.BASE_URL}/paper/arXiv:{arxiv_id}"

            # 指定需要的字段
            fields = [
                "paperId", "title", "abstract", "year", "authors",
                "citationCount", "referenceCount", "influentialCitationCount",
                "citations", "references", "fieldsOfStudy", "venue",
                "publicationDate", "url", "externalIds"
            ]

            params = {"fields": ",".join(fields)}

            logger.debug(f"请求 Semantic Scholar: {arxiv_id}")

            response = self._request(url, params=params)
            if not response:
                return None
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"成功获取论文: {arxiv_id}")
                return self._parse_paper(data)
            if response.status_code == 404:
                logger.warning(f"论文未找到: {arxiv_id}")
                return None
            logger.error(f"请求失败 {arxiv_id}: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"获取 Semantic Scholar 论文失败 {arxiv_id}: {str(e)}")
            return None

    def get_paper_citations(self, paper_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取论文的引用列表

        Args:
            paper_id: Semantic Scholar 论文ID
            limit: 最大返回数量

        Returns:
            List[Dict]: 引用论文列表
        """
        try:
            url = f"{self.BASE_URL}/paper/{paper_id}/citations"
            params = {
                "fields": "title,year,authors,citationCount",
                "limit": min(limit, 100)
            }

            response = self._request(url, params=params)
            if not response:
                return []
            if response.status_code == 200:
                data = response.json()
                citations = data.get("data", [])
                logger.debug(f"获取 {len(citations)} 条引用")
                return [self._parse_citation(c) for c in citations]
            logger.warning(f"获取引用失败: {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"获取引用失败: {str(e)}")
            return []

    def get_paper_references(self, paper_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取论文的参考文献列表

        Args:
            paper_id: Semantic Scholar 论文ID
            limit: 最大返回数量

        Returns:
            List[Dict]: 参考文献列表
        """
        try:
            url = f"{self.BASE_URL}/paper/{paper_id}/references"
            params = {
                "fields": "title,year,authors,citationCount",
                "limit": min(limit, 100)
            }

            response = self._request(url, params=params)
            if not response:
                return []
            if response.status_code == 200:
                data = response.json()
                references = data.get("data", [])
                logger.debug(f"获取 {len(references)} 条参考文献")
                return [self._parse_citation(r) for r in references]
            logger.warning(f"获取参考文献失败: {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"获取参考文献失败: {str(e)}")
            return []

    def search_author(self, author_name: str) -> Optional[Dict[str, Any]]:
        """
        搜索作者信息

        Args:
            author_name: 作者名称

        Returns:
            Dict: 作者信息，失败返回 None
        """
        try:
            url = f"{self.BASE_URL}/author/search"
            params = {
                "query": author_name,
                "fields": "authorId,name,affiliations,paperCount,citationCount,hIndex"
            }

            response = self._request(url, params=params)
            if not response:
                return None
            if response.status_code == 200:
                data = response.json()
                authors = data.get("data", [])
                if authors:
                    return self._parse_author(authors[0])
                logger.debug(f"作者未找到: {author_name}")
                return None
            logger.warning(f"搜索作者失败: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"搜索作者失败: {str(e)}")
            return None

    def search_papers(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索论文（用于基于主题发现候选作者）

        Args:
            query: 查询关键词/短语
            limit: 返回论文数量（<= 100）

        Returns:
            List[Dict]: 论文列表（包含作者与引用数等）
        """
        try:
            url = f"{self.BASE_URL}/paper/search"
            fields = ["paperId", "title", "abstract", "year", "venue", "citationCount", "authors", "url", "externalIds", "fieldsOfStudy"]
            params = {
                "query": query,
                "limit": min(limit, 100),
                "fields": ",".join(fields),
            }

            response = self._request(url, params=params)
            if not response:
                return []
            if response.status_code == 200:
                data = response.json()
                papers = data.get("data", []) or []
                return [self._parse_paper(p) for p in papers]
            logger.warning(f"搜索论文失败: {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"搜索论文失败: {str(e)}")
            return []

    def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        """
        获取作者详情

        Args:
            author_id: Semantic Scholar authorId

        Returns:
            Dict: 作者信息
        """
        try:
            url = f"{self.BASE_URL}/author/{author_id}"
            fields = [
                "authorId",
                "name",
                "affiliations",
                "homepage",
                "url",
                "paperCount",
                "citationCount",
                "hIndex",
                "aliases",
            ]
            params = {"fields": ",".join(fields)}
            response = self._request(url, params=params)
            if not response:
                return None
            if response.status_code == 200:
                return self._parse_author_detail(response.json())
            if response.status_code == 404:
                return None
            logger.warning(f"获取作者详情失败: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"获取作者详情失败: {str(e)}")
            return None

    def get_author_papers(self, author_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取作者论文列表（代表作/近期论文）

        Args:
            author_id: Semantic Scholar authorId
            limit: 返回数量（<= 1000，建议 <= 50 控制调用成本）

        Returns:
            List[Dict]: 作者论文列表
        """
        try:
            url = f"{self.BASE_URL}/author/{author_id}/papers"
            fields = ["paperId", "title", "abstract", "year", "venue", "citationCount", "url", "authors", "externalIds"]
            params = {
                "limit": min(limit, 1000),
                "fields": ",".join(fields),
            }

            response = self._request(url, params=params)
            if not response:
                return []
            if response.status_code == 200:
                data = response.json()
                papers = data.get("data", []) or []
                parsed = []
                for item in papers:
                    paper = item.get("paper") or item
                    parsed.append(self._parse_author_paper(paper))
                return parsed
            logger.warning(f"获取作者论文失败: {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"获取作者论文失败: {str(e)}")
            return []

    def enrich_paper(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        补充论文信息（引用、参考文献等）

        Args:
            arxiv_id: arXiv ID

        Returns:
            Dict: 补充后的论文信息
        """
        # 获取基本信息
        paper = self.get_paper_by_arxiv_id(arxiv_id)
        if not paper:
            return None

        # 获取引用和参考文献（限制数量以控制请求）
        paper_id = paper.get("semantic_scholar_id")
        if paper_id:
            paper["citations"] = self.get_paper_citations(paper_id, limit=50)
            paper["references"] = self.get_paper_references(paper_id, limit=50)

        return paper

    def batch_enrich_papers(
        self,
        arxiv_ids: List[str],
        max_papers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        批量补充论文信息

        Args:
            arxiv_ids: arXiv ID列表
            max_papers: 最大处理数量（用于控制API调用次数）

        Returns:
            List[Dict]: 补充后的论文列表
        """
        enriched_papers = []
        max_papers = max_papers or len(arxiv_ids)

        logger.info(f"开始批量补充 {min(max_papers, len(arxiv_ids))} 篇论文信息...")

        for idx, arxiv_id in enumerate(arxiv_ids[:max_papers]):
            try:
                paper = self.enrich_paper(arxiv_id)
                if paper:
                    enriched_papers.append(paper)

                if (idx + 1) % 10 == 0:
                    logger.info(f"进度: {idx + 1}/{min(max_papers, len(arxiv_ids))}")

            except Exception as e:
                logger.error(f"补充论文失败 {arxiv_id}: {str(e)}")

        logger.info(f"批量补充完成，成功 {len(enriched_papers)} 篇")
        return enriched_papers

    def _parse_paper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析论文数据"""
        # 提取作者
        authors = []
        for author in data.get("authors", []):
            authors.append({
                "id": author.get("authorId"),
                "name": author.get("name")
            })

        return {
            "semantic_scholar_id": data.get("paperId"),
            "title": data.get("title"),
            "abstract": data.get("abstract"),
            "year": data.get("year"),
            "authors": authors,
            "citation_count": data.get("citationCount", 0),
            "reference_count": data.get("referenceCount", 0),
            "influential_citation_count": data.get("influentialCitationCount", 0),
            "fields_of_study": data.get("fieldsOfStudy", []),
            "venue": data.get("venue"),
            "publication_date": data.get("publicationDate"),
            "url": data.get("url"),
            "external_ids": data.get("externalIds", {}),
            "source": "semantic_scholar"
        }

    def _parse_citation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析引用数据"""
        citing_paper = data.get("citingPaper") or data.get("citedPaper") or {}

        authors = []
        for a in citing_paper.get("authors", []) or []:
            authors.append({"id": a.get("authorId"), "name": a.get("name")})

        return {
            "paper_id": citing_paper.get("paperId"),
            "title": citing_paper.get("title"),
            "year": citing_paper.get("year"),
            "citation_count": citing_paper.get("citationCount", 0),
            "authors": authors,
        }

    def _parse_author(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析作者数据"""
        return {
            "id": data.get("authorId"),
            "name": data.get("name"),
            "affiliations": data.get("affiliations", []),
            "paper_count": data.get("paperCount", 0),
            "citation_count": data.get("citationCount", 0),
            "h_index": data.get("hIndex", 0),
            "source": "semantic_scholar"
        }

    def _parse_author_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": data.get("authorId"),
            "name": data.get("name"),
            "affiliations": data.get("affiliations", []) or [],
            "homepage": data.get("homepage"),
            "url": data.get("url"),
            "aliases": data.get("aliases", []) or [],
            "paper_count": data.get("paperCount", 0),
            "citation_count": data.get("citationCount", 0),
            "h_index": data.get("hIndex", 0),
            "source": "semantic_scholar",
        }

    def _parse_author_paper(self, data: Dict[str, Any]) -> Dict[str, Any]:
        authors = []
        for a in data.get("authors", []) or []:
            authors.append({"id": a.get("authorId"), "name": a.get("name")})
        return {
            "paper_id": data.get("paperId"),
            "title": data.get("title"),
            "abstract": data.get("abstract"),
            "year": data.get("year"),
            "venue": data.get("venue"),
            "citation_count": data.get("citationCount", 0),
            "url": data.get("url"),
            "external_ids": data.get("externalIds", {}) or {},
            "authors": authors,
        }


# 便捷函数
def enrich_arxiv_paper(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """
    补充 arXiv 论文信息

    Args:
        arxiv_id: arXiv ID

    Returns:
        Dict: 补充后的论文信息
    """
    crawler = SemanticScholarCrawler()
    return crawler.enrich_paper(arxiv_id)
