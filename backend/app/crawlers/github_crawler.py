"""
GitHub 项目爬虫
使用 GitHub API 搜索和获取开源项目信息
"""

import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
import time


class GitHubCrawler:
    """GitHub 爬虫类"""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, delay: float = 1.0):
        """
        初始化 GitHub 爬虫

        Args:
            token: GitHub Personal Access Token
            delay: 请求延迟（秒）
        """
        self.token = token
        self.delay = delay
        self.last_request_time = 0

        # 设置请求头
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Radiant-Academic-Assistant/1.0"
        }

        if token:
            self.headers["Authorization"] = f"token {token}"

    def _wait_for_rate_limit(self):
        """等待以遵守速率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        搜索 GitHub 仓库

        Args:
            query: 搜索查询
            sort: 排序字段 (stars, forks, updated)
            order: 排序顺序 (desc, asc)
            per_page: 每页结果数
            max_results: 最大结果数

        Returns:
            List[Dict]: 仓库列表
        """
        repositories = []

        try:
            self._wait_for_rate_limit()

            url = f"{self.BASE_URL}/search/repositories"
            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": min(per_page, 100)
            }

            logger.info(f"搜索 GitHub 仓库: {query}")

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])

                    for item in items[:max_results]:
                        repo_data = self._parse_repository(item)
                        repositories.append(repo_data)

                    logger.info(f"找到 {len(repositories)} 个仓库")
                    return repositories

                elif response.status_code == 403:
                    logger.warning("触发 GitHub API 速率限制")
                    return repositories

                else:
                    logger.error(f"搜索失败: {response.status_code}")
                    return repositories

        except Exception as e:
            logger.error(f"GitHub 搜索失败: {str(e)}")
            return repositories

    def get_repository(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        获取仓库详情

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            Dict: 仓库信息，失败返回 None
        """
        try:
            self._wait_for_rate_limit()

            url = f"{self.BASE_URL}/repos/{owner}/{repo}"

            logger.debug(f"获取仓库: {owner}/{repo}")

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_repository(data)
                else:
                    logger.warning(f"获取仓库失败: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"获取仓库失败: {str(e)}")
            return None

    def get_repository_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        获取仓库 README 内容

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            str: README 内容，失败返回 None
        """
        try:
            self._wait_for_rate_limit()

            url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    # README 内容是 base64 编码的
                    import base64
                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                    return content
                else:
                    return None

        except Exception as e:
            logger.error(f"获取 README 失败: {str(e)}")
            return None

    def search_paper_implementations(
        self,
        paper_title: str,
        arxiv_id: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索论文的代码实现

        Args:
            paper_title: 论文标题
            arxiv_id: arXiv ID（可选）
            max_results: 最大结果数

        Returns:
            List[Dict]: 相关仓库列表
        """
        # 构建搜索查询
        query_parts = []

        if arxiv_id:
            # 搜索包含 arXiv ID 的仓库
            query_parts.append(f'"{arxiv_id}"')

        # 提取论文标题中的关键词
        title_keywords = self._extract_keywords(paper_title)
        if title_keywords:
            query_parts.append(" ".join(title_keywords[:3]))  # 使用前3个关键词

        # 添加常用标签
        query_parts.append("implementation OR pytorch OR tensorflow")

        query = " ".join(query_parts)

        return self.search_repositories(query, max_results=max_results)

    def search_by_topics(
        self,
        topics: List[str],
        max_results: int = 30
    ) -> List[Dict[str, Any]]:
        """
        按主题搜索仓库

        Args:
            topics: 主题列表 (如 ['transformer', 'nlp'])
            max_results: 最大结果数

        Returns:
            List[Dict]: 仓库列表
        """
        # 构建查询：topic:transformer topic:nlp
        topic_query = " ".join([f"topic:{t}" for t in topics])
        query = f"{topic_query} stars:>100"  # 只搜索 star 数 > 100 的

        return self.search_repositories(query, max_results=max_results)

    def get_trending_ml_repos(self, max_results: int = 30) -> List[Dict[str, Any]]:
        """
        获取热门机器学习仓库

        Args:
            max_results: 最大结果数

        Returns:
            List[Dict]: 仓库列表
        """
        query = "machine-learning OR deep-learning OR pytorch OR tensorflow stars:>1000"
        return self.search_repositories(query, sort="stars", max_results=max_results)

    def _parse_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析仓库数据

        Args:
            data: GitHub API 返回的仓库数据

        Returns:
            Dict: 标准化的仓库数据
        """
        return {
            "id": f"github-{data.get('id')}",
            "github_id": data.get("id"),
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "github_url": data.get("html_url"),
            "clone_url": data.get("clone_url"),
            "homepage": data.get("homepage"),
            "language": data.get("language"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "watchers": data.get("watchers_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "topics": data.get("topics", []),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "pushed_at": data.get("pushed_at"),
            "size": data.get("size", 0),
            "license": data.get("license", {}).get("name") if data.get("license") else None,
            "owner": {
                "login": data.get("owner", {}).get("login"),
                "type": data.get("owner", {}).get("type"),
                "url": data.get("owner", {}).get("html_url")
            },
            "source": "github"
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 输入文本

        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取：移除常见停用词
        stopwords = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "was", "are",
            "via", "using", "based", "through"
        }

        words = text.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        return keywords

    def check_rate_limit(self) -> Dict[str, Any]:
        """
        检查 API 速率限制状态

        Returns:
            Dict: 速率限制信息
        """
        try:
            url = f"{self.BASE_URL}/rate_limit"

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    rate = data.get("rate", {})

                    return {
                        "limit": rate.get("limit"),
                        "remaining": rate.get("remaining"),
                        "reset": rate.get("reset"),
                        "used": rate.get("used")
                    }

        except Exception as e:
            logger.error(f"检查速率限制失败: {str(e)}")

        return {}


# 便捷函数
def search_github_repos(query: str, token: Optional[str] = None, max_results: int = 30) -> List[Dict[str, Any]]:
    """
    快捷搜索函数

    Args:
        query: 搜索查询
        token: GitHub Token
        max_results: 最大结果数

    Returns:
        List[Dict]: 仓库列表
    """
    crawler = GitHubCrawler(token=token)
    return crawler.search_repositories(query, max_results=max_results)
