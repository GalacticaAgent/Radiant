"""
审稿人服务
"""

from typing import List, Dict, Optional
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.db.neo4j import Neo4jConnection


class ReviewerService:
    """审稿人相关服务"""

    def __init__(
        self,
        llm_service: LLMService,
        graph_service: GraphService
    ):
        self.llm_service = llm_service
        self.graph_service = graph_service

    def recommend_reviewers(
        self,
        paper_content: str,
        paper_title: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        基于论文内容推荐审稿人

        Args:
            paper_content: 论文内容
            paper_title: 论文标题
            limit: 推荐数量

        Returns:
            List[Dict]: 推荐的审稿人列表
        """
        # 1. 使用LLM提取论文关键词
        keywords = self._extract_keywords(paper_content, paper_title)

        # 2. 在知识图谱中搜索相关研究者
        reviewers = []
        for keyword in keywords[:5]:  # 取前5个关键词
            results = self.graph_service.search_nodes(
                query=keyword,
                node_type="Person",
                limit=10
            )
            reviewers.extend(results)

        # 3. 去重并计算相关度分数
        unique_reviewers = {}
        for reviewer in reviewers:
            reviewer_id = reviewer.get("id")
            if reviewer_id not in unique_reviewers:
                unique_reviewers[reviewer_id] = {
                    "id": reviewer_id,
                    "name": reviewer.get("name", "Unknown"),
                    "affiliation": reviewer.get("affiliation", ""),
                    "research_interests": reviewer.get("research_interests", []),
                    "h_index": reviewer.get("h_index", 0),
                    "match_count": 1,
                    "matched_keywords": [keyword]
                }
            else:
                unique_reviewers[reviewer_id]["match_count"] += 1
                unique_reviewers[reviewer_id]["matched_keywords"].append(keyword)

        # 4. 排序（按匹配次数和h-index）
        sorted_reviewers = sorted(
            unique_reviewers.values(),
            key=lambda x: (x["match_count"], x.get("h_index", 0)),
            reverse=True
        )

        return sorted_reviewers[:limit]

    def _extract_keywords(
        self,
        content: str,
        title: Optional[str] = None
    ) -> List[str]:
        """
        从论文中提取关键词

        Args:
            content: 论文内容
            title: 论文标题

        Returns:
            List[str]: 关键词列表
        """
        # 构建提示词
        prompt = f"请从以下论文中提取5-10个最重要的研究领域关键词（如：自然语言处理、计算机视觉、Transformer等）。\n\n"

        if title:
            prompt += f"标题: {title}\n\n"

        # 只使用论文的前2000个字符来提取关键词
        prompt += f"内容摘要:\n{content[:2000]}\n\n"
        prompt += "请只返回关键词列表，每个关键词一行，不要包含其他内容。"

        try:
            response = self.llm_service.chat_with_context(
                user_message=prompt,
                system_prompt="你是一个学术论文分析专家，擅长提取论文的核心研究主题。",
                history=[]
            )

            # 解析响应，提取关键词
            keywords = [
                line.strip().strip('-').strip('*').strip()
                for line in response.split('\n')
                if line.strip() and len(line.strip()) > 2
            ]

            return keywords[:10]  # 最多返回10个关键词

        except Exception as e:
            print(f"关键词提取失败: {e}")
            # 如果LLM失败，返回一些基于标题的简单关键词
            if title:
                return [word for word in title.split() if len(word) > 3][:5]
            return []

    def generate_reviewer_profile(
        self,
        reviewer_id: str,
        reviewer_name: str
    ) -> str:
        """
        生成审稿人画像

        Args:
            reviewer_id: 审稿人ID（知识图谱中）
            reviewer_name: 审稿人姓名

        Returns:
            str: 审稿人画像
        """
        # 1. 从知识图谱获取审稿人的论文
        papers = self.graph_service.get_researcher_papers(reviewer_id, limit=20)

        # 2. 提取论文信息
        paper_titles = [p.get("title", "") for p in papers if p.get("title")]
        research_interests = []

        # 尝试从论文中提取研究兴趣
        for paper in papers[:5]:  # 取最近5篇论文
            if "abstract" in paper:
                research_interests.append(paper["abstract"][:200])

        # 3. 使用LLM生成画像
        profile = self.llm_service.generate_reviewer_profile(
            reviewer_name=reviewer_name,
            papers=paper_titles,
            research_interests=research_interests
        )

        return profile

    def generate_review(
        self,
        paper_content: str,
        reviewer_profile: str,
        reviewer_name: str,
        paper_title: Optional[str] = None
    ) -> Dict:
        """
        生成审稿意见

        Args:
            paper_content: 论文内容
            reviewer_profile: 审稿人画像
            reviewer_name: 审稿人姓名
            paper_title: 论文标题

        Returns:
            Dict: 审稿意见（包含content, rating, strengths, weaknesses, suggestions）
        """
        raw = self.llm_service.generate_review(
            paper_content=paper_content,
            reviewer_profile=reviewer_profile,
            reviewer_name=reviewer_name
        )
        strengths = raw.get("strengths")
        weaknesses = raw.get("weaknesses")
        suggestions = raw.get("suggestions")
        rating_raw = raw.get("overall_score") or raw.get("rating")
        confidence = raw.get("confidence")
        recommendation = raw.get("recommendation")

        rating: Optional[int] = None
        try:
            if rating_raw is not None:
                if isinstance(rating_raw, (int, float)):
                    rating = int(rating_raw)
                else:
                    import re

                    m = re.search(r"\d+", str(rating_raw))
                    rating = int(m.group(0)) if m else None
        except Exception:
            rating = None
        confidence = raw.get("confidence")

        if "review_markdown" in raw:
            review_content = raw["review_markdown"]
        elif "raw_response" in raw:
            review_content = raw["raw_response"]
        else:
            sections = []
            if strengths:
                sections.append("优点：\n" + "\n".join([f"- {s}" for s in strengths]))
            if weaknesses:
                sections.append("缺点：\n" + "\n".join([f"- {w}" for w in weaknesses]))
            if suggestions:
                sections.append("建议：\n" + "\n".join([f"- {s}" for s in suggestions]))
            if rating is not None:
                sections.append(f"评分：{rating}")
            review_content = "\n\n".join(sections).strip()

        try:
            import re

            review_content = re.sub(r"^\s*[•\-\*]\s*$", "", review_content, flags=re.MULTILINE).strip()
        except Exception:
            pass

        has_overall = False
        try:
            import re

            has_overall = bool(re.search(r"(总体建议|Recommendation|Overall\s+Recommendation)", review_content, re.IGNORECASE))
        except Exception:
            has_overall = False

        if not has_overall and (rating is not None or confidence or recommendation):
            parts = ["### 总体建议"]
            if rating is not None:
                parts.append(f"- Rating: {rating}/10")
            if confidence:
                parts.append(f"- Confidence: {confidence}")
            if recommendation:
                parts.append(f"- Recommendation: {recommendation}")
            parts.append("")
            parts.append(review_content)
            review_content = "\n".join([p for p in parts if p is not None]).strip()

        return {
            "reviewer_name": reviewer_name,
            "review_content": review_content,
            "rating": rating,
            "confidence": confidence,
            "recommendation": recommendation,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
        }

    def generate_modification_suggestions(
        self,
        paper_content: str,
        reviews: List[Dict],
        paper_title: Optional[str] = None
    ) -> List[Dict]:
        """
        基于审稿意见生成修改建议

        Args:
            paper_content: 论文内容
            reviews: 审稿意见列表
            paper_title: 论文标题

        Returns:
            List[Dict]: 修改建议列表
        """
        suggestions = []

        # 整合所有审稿意见
        all_weaknesses = []
        all_suggestions = []

        for review in reviews:
            if "weaknesses" in review:
                all_weaknesses.extend(review["weaknesses"])
            if "suggestions" in review:
                all_suggestions.extend(review["suggestions"])

        # 构建提示词
        prompt = f"""基于以下审稿意见，为论文提供具体的修改建议。

论文标题: {paper_title or '未提供'}

主要问题:
{chr(10).join(f"- {w}" for w in all_weaknesses[:10])}

审稿人建议:
{chr(10).join(f"- {s}" for s in all_suggestions[:10])}

论文内容摘要:
{paper_content[:1500]}

请提供5-10条具体的修改建议，每条建议包括：
1. 修改位置（章节）
2. 具体问题
3. 修改建议
4. 优先级（高/中/低）

请以JSON格式返回，格式如下：
[
  {{
    "section": "摘要",
    "issue": "问题描述",
    "suggestion": "具体修改建议",
    "priority": "高"
  }}
]
"""

        try:
            response = self.llm_service.chat_with_context(
                user_message=prompt,
                system_prompt="你是一个专业的学术论文编辑，擅长根据审稿意见提供具体的修改建议。",
                history=[]
            )

            # 尝试解析JSON响应
            import json
            import re

            # 提取JSON部分（可能被包裹在markdown代码块中）
            json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接查找JSON数组
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = "[]"

            suggestions = json.loads(json_str)

        except Exception as e:
            print(f"修改建议生成失败: {e}")
            # 返回基本建议
            suggestions = [
                {
                    "section": "全文",
                    "issue": "需要根据审稿意见进行修改",
                    "suggestion": "; ".join(all_suggestions[:3]) if all_suggestions else "请仔细阅读审稿意见",
                    "priority": "高"
                }
            ]

        return suggestions
