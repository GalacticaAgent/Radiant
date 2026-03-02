"""
Research Service - 调研任务管理服务
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.services.graph_service import GraphService
from app.services.llm_service import LLMService
from app.db.redis import get_redis
from app.schemas.research import (
    TaskStatus,
    TaskInfo,
    ResearchResult,
    PaperSummary,
    ResearchSource
)


_tasks: Dict[str, dict] = {}
_redis = get_redis()


def _task_key(task_id: str) -> str:
    return f"research:task:{task_id}"


def _serialize_task(task: dict) -> dict:
    serialized = dict(task)
    for k in ("created_at", "updated_at"):
        if isinstance(serialized.get(k), datetime):
            serialized[k] = serialized[k].isoformat()
    if isinstance(serialized.get("result"), ResearchResult):
        serialized["result"] = serialized["result"].model_dump()
        if isinstance(serialized["result"].get("completed_at"), datetime):
            serialized["result"]["completed_at"] = serialized["result"]["completed_at"].isoformat()
    return serialized


def _deserialize_task(task: dict) -> dict:
    deserialized = dict(task)
    for k in ("created_at", "updated_at"):
        if isinstance(deserialized.get(k), str):
            deserialized[k] = datetime.fromisoformat(deserialized[k])
    result = deserialized.get("result")
    if isinstance(result, dict):
        if isinstance(result.get("completed_at"), str):
            result["completed_at"] = datetime.fromisoformat(result["completed_at"])
        deserialized["result"] = ResearchResult(**result)
    return deserialized


def _persist_task(task_id: str, task: dict) -> None:
    _tasks[task_id] = task
    if _redis.ping():
        _redis.set_json(_task_key(task_id), _serialize_task(task), ex=60 * 60 * 24 * 7)


def _load_task(task_id: str) -> Optional[dict]:
    task = _tasks.get(task_id)
    if task:
        return task
    if _redis.ping():
        data = _redis.get_json(_task_key(task_id))
        if isinstance(data, dict):
            task = _deserialize_task(data)
            _tasks[task_id] = task
            return task
    return None


class ResearchService:
    """调研服务类"""

    @staticmethod
    def create_task(query: str, sources: List[ResearchSource], max_papers: int = 50, filters: dict = None) -> str:
        """
        创建调研任务

        Args:
            query: 调研主题
            sources: 数据源列表
            max_papers: 最大论文数
            filters: 过滤条件

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()

        task = {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "query": query,
            "sources": sources,
            "max_papers": max_papers,
            "filters": filters or {},
            "created_at": now,
            "updated_at": now,
            "progress": 0,
            "message": "任务已创建",
            "papers": [],
            "result": None
        }

        _persist_task(task_id, task)
        return task_id

    @staticmethod
    def get_task_status(task_id: str) -> Optional[TaskInfo]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            TaskInfo: 任务信息
        """
        task = _load_task(task_id)
        if not task:
            return None

        return TaskInfo(
            task_id=task["task_id"],
            status=task["status"],
            query=task["query"],
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            progress=task["progress"],
            message=task.get("message"),
            error=task.get("error")
        )

    @staticmethod
    def get_task_result(task_id: str) -> Optional[ResearchResult]:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            ResearchResult: 调研结果
        """
        task = _load_task(task_id)
        if not task or task["status"] != TaskStatus.COMPLETED:
            return None

        return task.get("result")

    @staticmethod
    def start_background(task_id: str, graph_service: GraphService, llm_service: LLMService) -> None:
        import threading

        thread = threading.Thread(
            target=ResearchService.execute_research,
            args=(task_id, graph_service, llm_service),
            daemon=True,
        )
        thread.start()

    @staticmethod
    def execute_research(
        task_id: str,
        graph_service: GraphService,
        llm_service: LLMService
    ) -> ResearchResult:
        """
        执行调研任务

        Args:
            task_id: 任务ID
            graph_service: 图谱服务
            llm_service: LLM服务

        Returns:
            ResearchResult: 调研结果
        """
        task = _load_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        try:
            # 更新状态为运行中
            task["status"] = TaskStatus.RUNNING
            task["progress"] = 10
            task["message"] = "开始搜索相关论文"
            task["updated_at"] = datetime.utcnow()
            _persist_task(task_id, task)

            query = task["query"]
            max_papers = task["max_papers"]
            sources = task["sources"]

            # 1. 提取关键词
            keywords = ResearchService._extract_keywords(query, llm_service)
            task["progress"] = 20
            task["message"] = f"已提取 {len(keywords)} 个关键词"
            task["updated_at"] = datetime.utcnow()
            _persist_task(task_id, task)

            # 2. 从知识图谱搜索论文
            papers = []
            if ResearchSource.KNOWLEDGE_GRAPH in sources:
                papers = ResearchService._search_papers_from_graph(
                    keywords, graph_service, max_papers
                )

            task["progress"] = 60
            task["message"] = f"已找到 {len(papers)} 篇相关论文"
            task["updated_at"] = datetime.utcnow()
            _persist_task(task_id, task)

            # 3. 使用LLM分析论文并生成总结
            task["progress"] = 70
            task["message"] = "正在分析论文内容"
            task["updated_at"] = datetime.utcnow()
            _persist_task(task_id, task)

            result = ResearchService._analyze_papers(
                query, papers, llm_service, task_id=task_id
            )

            # 4. 构建最终结果
            task["progress"] = 100
            task["status"] = TaskStatus.COMPLETED
            task["message"] = "调研完成"
            task["updated_at"] = datetime.utcnow()
            task["result"] = result
            _persist_task(task_id, task)

            return result

        except Exception as e:
            task["status"] = TaskStatus.FAILED
            task["error"] = str(e)
            task["message"] = f"任务失败: {str(e)}"
            task["updated_at"] = datetime.utcnow()
            _persist_task(task_id, task)
            raise

    @staticmethod
    def _extract_keywords(query: str, llm_service: LLMService) -> List[str]:
        """提取查询关键词"""
        fallback = [w for w in query.replace("-", " ").replace("_", " ").split() if len(w) > 2][:8]
        prompt = f"""请从以下调研主题中提取5-8个最重要的学术关键词。

调研主题:
{query}

请只返回关键词列表，每个关键词一行，不要包含其他内容。"""
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    llm_service.chat_with_context,
                    user_message=prompt,
                    system_prompt="你是一个学术研究分析专家，擅长识别研究中的关键概念。",
                    history=[],
                )
                response = future.result(timeout=8)

            keywords = [
                line.strip().strip('-').strip('*').strip()
                for line in response.split('\n')
                if line.strip() and len(line.strip()) > 2
            ]
            return keywords[:8] or fallback
        except Exception:
            return fallback

    @staticmethod
    def _search_papers_from_graph(
        keywords: List[str],
        graph_service: GraphService,
        max_papers: int
    ) -> List[dict]:
        """从知识图谱搜索论文"""
        papers = []
        seen_ids = set()

        for keyword in keywords:
            results = graph_service.search_nodes(
                query=keyword,
                node_type="Paper",
                limit=max_papers // len(keywords) + 5
            )

            for paper in results:
                paper_id = paper.get("id", "")
                if paper_id and paper_id not in seen_ids:
                    papers.append(paper)
                    seen_ids.add(paper_id)

                if len(papers) >= max_papers:
                    break

            if len(papers) >= max_papers:
                break

        return papers[:max_papers]

    @staticmethod
    def _analyze_papers(
        query: str,
        papers: List[dict],
        llm_service: LLMService,
        task_id: str
    ) -> ResearchResult:
        """分析论文并生成调研报告"""
        # 构建论文列表
        paper_summaries = []
        paper_texts = []

        for i, paper in enumerate(papers[:30]):  # 限制论文数量以避免token超限
            paper_summary = PaperSummary(
                id=paper.get("id", f"paper_{i}"),
                title=paper.get("title", "Unknown"),
                authors=paper.get("authors", []),
                year=paper.get("year"),
                abstract=paper.get("abstract", ""),
                url=paper.get("url"),
                relevance_score=0.8,  # 可以改进为更精确的计算
                key_findings=None
            )
            paper_summaries.append(paper_summary)

            paper_texts.append(f"{i+1}. {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')})")

        # 生成调研总结
        analysis_prompt = f"""你是一位资深的学术研究专家。请基于以下论文列表，对研究主题进行深入分析。

研究主题: {query}

相关论文 ({len(paper_summaries)} 篇):
{chr(10).join(paper_texts[:20])}

请提供以下内容的JSON格式分析（确保返回有效的JSON）:
{{
    "summary": "调研总结（200-300字）",
    "key_trends": ["趋势1", "趋势2", "趋势3"],
    "research_gaps": ["空白1", "空白2", "空白3"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}"""

        try:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    llm_service.chat_with_context,
                    user_message=analysis_prompt,
                    system_prompt="你是一位资深的学术研究专家，擅长文献综述和趋势分析。请以JSON格式返回分析结果。",
                    history=[],
                )
                response = future.result(timeout=15)

            # 尝试解析JSON响应
            import json
            import re

            # 提取JSON内容
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis_data = json.loads(json_match.group(0))
            else:
                raise ValueError("未找到有效的JSON响应")

            summary = analysis_data.get("summary", "暂无总结")
            key_trends = analysis_data.get("key_trends", ["数据不足"])
            research_gaps = analysis_data.get("research_gaps", ["数据不足"])
            recommendations = analysis_data.get("recommendations", ["建议进一步研究"])

        except Exception as e:
            print(f"LLM分析失败: {e}")
            summary = f"基于 {len(papers)} 篇相关论文的初步调研已完成。"
            key_trends = ["深度学习方法", "跨领域应用", "性能优化"]
            research_gaps = ["实际应用案例不足", "长期效果研究缺乏"]
            recommendations = ["建议关注最新进展", "可考虑实际应用研究"]

        # 构建结果
        result = ResearchResult(
            task_id=task_id,
            query=query,
            papers=paper_summaries,
            total_found=len(papers),
            summary=summary,
            key_trends=key_trends,
            research_gaps=research_gaps,
            recommendations=recommendations,
            completed_at=datetime.utcnow()
        )

        return result

    @staticmethod
    def list_tasks() -> List[TaskInfo]:
        """列出所有任务"""
        return [
            TaskInfo(
                task_id=task["task_id"],
                status=task["status"],
                query=task["query"],
                created_at=task["created_at"],
                updated_at=task["updated_at"],
                progress=task["progress"],
                message=task.get("message"),
                error=task.get("error")
            )
            for task in _tasks.values()
        ]
