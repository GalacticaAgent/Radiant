"""
对话 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import uuid4
import json
import logging
from app.db.postgres import get_db
from app.db.neo4j import get_neo4j
from app.db.redis import get_redis
from app.api.deps import get_current_user, get_current_user_from_query
from app.models.user import User
from app.models.conversation import Conversation, ChatSession
from app.services.chat_service import ChatService
from app.services.llm_service import get_llm_service, LLMService
from app.services.graph_service import get_graph_service, GraphService
from app.db.neo4j import Neo4jConnection
from app.db.redis import RedisClient
from app.services.paper_service import PaperService
from app.schemas.chat import (
    ChatRequest, ChatResponse, ConversationHistoryResponse, ConversationMessage, ReferenceItem,
    SessionListResponse, RenameSessionRequest, PinSessionRequest, SessionSchema, AppendMessageRequest, AppendMessageResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_chat_service(
    db: Session = Depends(get_db),
    neo4j_conn: Neo4jConnection = Depends(get_neo4j),
    redis_client: RedisClient = Depends(get_redis),
    llm_service: LLMService = Depends(get_llm_service)
) -> ChatService:
    """获取对话服务"""
    graph_service = get_graph_service(neo4j_conn)
    return ChatService(db, llm_service, graph_service, redis_client)


@router.get("/sessions", response_model=SessionListResponse)
def get_sessions(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取当前用户的所有会话"""
    try:
        sessions = chat_service.get_user_sessions(str(current_user.id))
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )


@router.put("/session/{session_id}", response_model=SessionSchema)
def rename_session(
    session_id: str,
    request: RenameSessionRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """重命名会话"""
    try:
        # Check ownership
        session = chat_service.get_session(session_id)
        if not session or str(session.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="会话不存在")
        
        updated_session = chat_service.update_session(session_id, title=request.title)
        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重命名会话失败: {str(e)}"
        )


@router.put("/session/{session_id}/pin", response_model=SessionSchema)
def pin_session(
    session_id: str,
    request: PinSessionRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """置顶/取消置顶会话"""
    try:
        # Check ownership
        session = chat_service.get_session(session_id)
        if not session or str(session.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="会话不存在")
        
        updated_session = chat_service.update_session(session_id, is_pinned=request.pinned)
        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新会话状态失败: {str(e)}"
        )


@router.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """删除会话"""
    try:
        # Check ownership
        session = chat_service.get_session(session_id)
        if not session or str(session.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="会话不存在")
        
        chat_service.delete_session(session_id)
        return {"message": "会话已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )


@router.post("/send", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    发送消息并获得 AI 回复

    - **message**: 用户消息（1-5000字符）
    - **session_id**: 会话ID（可选，不提供会自动生成）
    - **search_graph**: 是否搜索知识图谱（默认 true）
    """
    # 生成会话ID（如果未提供）
    session_id = request.session_id or str(uuid4())

    try:
        # 处理消息
        response_text, references = chat_service.chat(
            str(current_user.id),
            session_id,
            request.message,
            search_graph=request.search_graph
        )

        return ChatResponse(
            message_id=str(uuid4()),
            content=response_text,
            references=references or [],
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理消息时出错: {str(e)}"
        )


@router.post("/send-file", response_model=ChatResponse)
async def send_message_with_file(
    message: str = Form(..., description="用户消息"),
    session_id: Optional[str] = Form(None, description="会话ID（可选）"),
    search_graph: bool = Form(True, description="是否搜索知识图谱"),
    file: UploadFile = File(..., description="上传的 PDF/DOCX"),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    sid = session_id or str(uuid4())
    filename = file.filename or "uploaded"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    try:
        raw = await file.read()
        if ext == "pdf" or file.content_type == "application/pdf":
            extracted = await run_in_threadpool(PaperService.extract_text_from_pdf, raw)
        elif ext == "docx" or file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            extracted = await run_in_threadpool(PaperService.extract_text_from_docx, raw)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 PDF 或 DOCX 文件")

        extracted = (extracted or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not extracted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未能从文件中提取到文本内容")

        clip = extracted[:8000]
        user_message = (
            (message or "").strip()
            + "\n\n"
            + "【用户上传附件】\n"
            + f"- 文件名：{filename}\n"
            + "- 内容摘录：\n"
            + clip
        ).strip()

        response_text, references = chat_service.chat(
            str(current_user.id),
            sid,
            user_message,
            search_graph=bool(search_graph),
        )

        return ChatResponse(
            message_id=str(uuid4()),
            content=response_text,
            references=references or [],
            session_id=sid,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"处理消息时出错: {str(e)}")


@router.post("/append", response_model=AppendMessageResponse)
def append_message(
    request: AppendMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        role = (request.role or "").strip()
        if role not in {"user", "assistant", "system"}:
            raise HTTPException(status_code=422, detail="role 必须是 user/assistant/system")
        existing = chat_service.get_session(request.session_id)
        if existing and str(existing.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="会话不存在")
        conv = chat_service.save_conversation(
            str(current_user.id),
            request.session_id,
            role,
            request.content,
            references=request.references,
        )
        return AppendMessageResponse(session_id=request.session_id, created_at=conv.created_at.isoformat())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"追加消息失败: {str(e)}",
        )


@router.get("/history", response_model=ConversationHistoryResponse)
def get_conversation_history(
    session_id: str = Query(..., description="会话ID"),
    limit: int = Query(50, ge=1, le=100, description="返回消息数量限制"),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取对话历史

    - **session_id**: 会话ID（必需）
    - **limit**: 返回消息数量限制（1-100，默认50）
    """
    try:
        messages = chat_service.get_session_history(
            str(current_user.id),
            session_id,
            limit=limit
        )

        return ConversationHistoryResponse(
            session_id=session_id,
            messages=[
                ConversationMessage(
                    role=msg["role"],
                    content=msg["content"],
                    references=msg.get("references"),
                    created_at=msg["created_at"]
                )
                for msg in messages
            ],
            total=len(messages)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.get("/stream")
def stream_chat(
    message: str = Query(..., min_length=1, description="用户消息"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    current_user: User = Depends(get_current_user_from_query),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    流式对话

    - **message**: 用户消息
    - **session_id**: 会话ID（可选）

    返回流式响应，实时返回生成的文本。
    使用 Server-Sent Events (SSE) 格式，返回 JSON 数据。
    """
    session_id = session_id or str(uuid4())

    def generate():
        logger.error("===== TESTING: Starting SSE stream generation =====")
        try:
            for chunk in chat_service.stream_chat(
                str(current_user.id),
                session_id,
                message
            ):
                # 发送 JSON 格式的数据
                data = json.dumps({"content": chunk, "done": False})
                logger.error(f"===== TESTING: Sending SSE data: {data} =====")
                yield f"data: {data}\n\n"

            # 发送完成信号
            done_signal = json.dumps({"content": "", "done": True})
            logger.error(f"===== TESTING: Sending done signal: {done_signal} =====")
            yield f"data: {done_signal}\n\n"
        except Exception as e:
            # 发送错误信息
            logger.error(f"===== TESTING: Error in SSE stream: {e} =====")
            error_data = json.dumps({"content": f"ERROR: {str(e)}", "done": True})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/clear")
def clear_session(
    session_id: str = Query(..., description="会话ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    清除对话会话

    - **session_id**: 会话ID

    删除指定会话的所有对话记录。
    """
    from app.models.conversation import Conversation

    try:
        # 删除用户在该会话中的所有消息
        db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.session_id == session_id
        ).delete()
        db.commit()

        return {"message": "会话已清除"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除会话失败: {str(e)}"
        )
