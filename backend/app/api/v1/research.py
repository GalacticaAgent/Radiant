"""
Research 调研 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.user import User
from app.api.deps import get_current_user, get_llm_service, get_graph_service
from app.services.research_service import ResearchService
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.schemas.research import (
    ResearchRequest,
    TaskInfo,
    ResearchResult,
    ResearchStartResponse,
    ResearchSource
)

router = APIRouter(tags=["research"])


@router.post("/start", response_model=ResearchStartResponse)
def start_research(
    request: ResearchRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    启动调研任务

    - **query**: 调研主题或问题（必填）
    - **sources**: 数据源列表（默认: 知识图谱）
    - **max_papers**: 最大论文数（1-200，默认: 50）
    - **filters**: 过滤条件（可选）

    返回任务ID，可用于查询状态和结果
    """
    try:
        # 创建任务
        task_id = ResearchService.create_task(
            query=request.query,
            sources=request.sources,
            max_papers=request.max_papers,
            filters=request.filters
        )

        ResearchService.start_background(task_id, graph_service, llm_service)

        return ResearchStartResponse(
            task_id=task_id,
            status="pending",
            message="调研任务已启动，请使用任务ID查询进度"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动调研任务失败: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TaskInfo)
def get_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询调研任务状态

    - **task_id**: 任务ID

    返回任务当前的状态、进度和消息
    """
    task_info = ResearchService.get_task_status(task_id)

    if not task_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )

    return task_info


@router.get("/result/{task_id}", response_model=ResearchResult)
def get_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取调研任务结果

    - **task_id**: 任务ID

    返回完整的调研结果，包括论文列表、总结、趋势等
    """
    result = ResearchService.get_task_result(task_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在或未完成: {task_id}"
        )

    return result


@router.get("/tasks", response_model=List[TaskInfo])
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    列出所有调研任务

    返回当前用户的所有调研任务列表（包括待处理、进行中、已完成的任务）
    """
    return ResearchService.list_tasks()
