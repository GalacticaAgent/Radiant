"""
Idea 验证 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.postgres import get_db
from app.models.user import User
from app.api.deps import get_current_user, get_llm_service, get_graph_service
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.schemas.idea import (
    IdeaValidationRequest,
    IdeaValidationResult,
    RelatedPaper
)

router = APIRouter(tags=["ideas"])


@router.post("/validate", response_model=IdeaValidationResult)
def validate_idea(
    request: IdeaValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    验证研究 Idea 的可行性

    - **idea**: 研究想法（必填）
    - **background**: 背景信息（可选）

    返回可行性评分、创新性评分、相关论文和详细分析
    """
    try:
        # 1. 提取关键词
        keywords = _extract_keywords(request.idea, llm_service)

        # 2. 在知识图谱中搜索相关论文
        related_papers = []
        for keyword in keywords[:5]:
            results = graph_service.search_nodes(
                query=keyword,
                node_type="Paper",
                limit=5
            )

            for paper in results:
                if len(related_papers) < 10:
                    related_papers.append(
                        RelatedPaper(
                            id=paper.get("id", ""),
                            title=paper.get("title", ""),
                            authors=paper.get("authors", []),
                            year=paper.get("year"),
                            relevance=0.8  # 可以改进为更精确的计算
                        )
                    )

        # 3. 使用LLM评估可行性
        analysis = llm_service.evaluate_idea(request.idea, [p.title for p in related_papers])

        # 4. 解析LLM响应
        result = _parse_evaluation_result(analysis, request.idea, related_papers)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Idea验证失败: {str(e)}"
        )


def _extract_keywords(idea: str, llm_service: LLMService) -> list:
    """
    从Idea中提取关键词
    """
    prompt = f"""请从以下研究想法中提取5-8个最重要的关键词或研究主题。

研究想法:
{idea}

请只返回关键词列表，每个关键词一行，不要包含其他内容。"""

    try:
        response = llm_service.chat_with_context(
            user_message=prompt,
            system_prompt="你是一个学术研究分析专家，擅长识别研究中的关键概念。",
            history=[]
        )

        keywords = [
            line.strip().strip('-').strip('*').strip()
            for line in response.split('\n')
            if line.strip() and len(line.strip()) > 2
        ]

        return keywords[:8]

    except Exception as e:
        print(f"关键词提取失败: {e}")
        return []


def _parse_evaluation_result(
    analysis: dict,
    idea: str,
    related_papers: list
) -> IdeaValidationResult:
    """
    解析LLM的评估结果并构建IdeaValidationResult
    """
    # 提取分数（确保在0-10范围内）
    feasibility_score = float(analysis.get("feasibility_score", 5))
    if 0 <= feasibility_score <= 1:
        feasibility_score *= 10
    feasibility_score = max(0, min(10, feasibility_score))

    innovation_score = float(analysis.get("innovation_score", 5))
    if 0 <= innovation_score <= 1:
        innovation_score *= 10
    innovation_score = max(0, min(10, innovation_score))

    # 获取其他字段
    technical_difficulty = analysis.get("technical_difficulty", "中")
    estimated_time = analysis.get("estimated_time", "6个月")

    strengths = analysis.get("strengths", [
        "研究方向明确",
        "有明确的应用价值"
    ])

    challenges = analysis.get("challenges", [
        "技术实现存在难度",
        "需要获取足够的数据"
    ])

    recommendations = analysis.get("recommendations", [
        "建议先查阅相关文献",
        "可以考虑与领域专家合作",
        "建议制定详细的研究计划"
    ])

    research_directions = analysis.get("research_directions", [
        "深度学习应用",
        "自然语言处理",
        "知识图谱"
    ])

    detailed_analysis = analysis.get("detailed_analysis", f"""
关于您的研究想法 "{idea[:100]}..." 的分析：

可行性评分：{feasibility_score:.1f}/10
创新性评分：{innovation_score:.1f}/10

该想法在技术上的难度等级为{technical_difficulty}，预计完成时间约为{estimated_time}。

我们在知识图谱中找到了{len(related_papers)}篇相关的研究论文，这些论文可以为您的研究提供重要参考。

建议您：
1. 深入阅读相关论文，了解当前研究进展
2. 与领域内的研究人员进行交流和合作
3. 制定详细的研究计划和时间表
4. 考虑申请相关的科研基金支持
""")

    return IdeaValidationResult(
        feasibility_score=feasibility_score,
        innovation_score=innovation_score,
        technical_difficulty=technical_difficulty,
        estimated_time=estimated_time,
        strengths=strengths,
        challenges=challenges,
        recommendations=recommendations,
        related_papers=related_papers,
        research_directions=research_directions,
        detailed_analysis=detailed_analysis
    )
