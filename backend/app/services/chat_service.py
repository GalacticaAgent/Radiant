"""
对话服务
提供聊天和对话管理功能
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, ChatSession
from app.models.user import User
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.db.redis import RedisClient
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatService:
    """对话服务类"""

    def __init__(
        self,
        db: Session,
        llm_service: LLMService,
        graph_service: GraphService,
        redis_client: RedisClient
    ):
        """
        初始化对话服务

        Args:
            db: 数据库会话
            llm_service: LLM 服务
            graph_service: 图谱服务
            redis_client: Redis 客户端
        """
        self.db = db
        self.llm = llm_service
        self.graph = graph_service
        self.redis = redis_client

    def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """获取用户的所有会话"""
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.is_pinned.desc(), ChatSession.updated_at.desc()).all()

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取单个会话"""
        return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()

    def update_session(self, session_id: str, title: Optional[str] = None, is_pinned: Optional[bool] = None) -> Optional[ChatSession]:
        """更新会话"""
        session = self.get_session(session_id)
        if session:
            if title is not None:
                session.title = title
            if is_pinned is not None:
                session.is_pinned = is_pinned
            session.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session = self.get_session(session_id)
        if session:
            # Cascade delete conversations
            self.db.query(Conversation).filter(Conversation.session_id == session_id).delete()
            self.db.delete(session)
            self.db.commit()
            return True
        return False

    def get_session_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取会话历史

        Args:
            user_id: 用户ID
            session_id: 会话ID
            limit: 返回记录数量限制

        Returns:
            List[Dict]: 对话历史列表
        """
        conversations = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id
        ).order_by(Conversation.created_at.asc()).limit(limit).all()

        return [
            {
                "role": conv.role,
                "content": conv.content,
                "references": conv.ref_data,
                "created_at": conv.created_at.isoformat()
            }
            for conv in conversations
        ]

    def save_conversation(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        references: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        保存对话记录

        Args:
            user_id: 用户ID
            session_id: 会话ID
            role: 角色（user/assistant/system）
            content: 内容
            references: 引用数据（可选）

        Returns:
            Conversation: 保存的对话记录
        """
        # 检查并创建会话元数据
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            # 自动生成标题
            title = "New Chat"
            if role == "user":
                title = content[:30] + "..." if len(content) > 30 else content
            
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                title=title
            )
            self.db.add(session)
        else:
            # 更新会话时间
            session.updated_at = datetime.utcnow()

        conversation = Conversation(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            ref_data=references
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def extract_keywords_from_message(self, message: str) -> List[str]:
        """
        从用户消息中提取关键词

        Args:
            message: 用户消息

        Returns:
            List[str]: 关键词列表
        """
        try:
            keywords = self.llm.extract_keywords(message, max_keywords=5)
            return keywords
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return []

    def search_context_from_graph(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        从知识图谱中搜索相关上下文

        Args:
            keywords: 关键词列表
            limit: 结果限制

        Returns:
            Tuple: (论文列表, 研究者列表)
        """
        papers = []
        researchers = []

        for keyword in keywords:
            # 搜索论文
            paper_results = self.graph.search_nodes(
                keyword,
                node_type="Paper",
                limit=limit // len(keywords)
            )
            papers.extend(paper_results)

            # 搜索研究者
            researcher_results = self.graph.search_nodes(
                keyword,
                node_type="Person",
                limit=limit // len(keywords)
            )
            researchers.extend(researcher_results)

        # 去重
        papers = list({p.get("id"): p for p in papers}.values())
        researchers = list({r.get("id"): r for r in researchers}.values())

        return papers[:limit], researchers[:limit // 2]

    def build_system_prompt(self, papers: List[Dict[str, Any]]) -> str:
        """
        构建系统提示词

        Args:
            papers: 相关论文列表

        Returns:
            str: 系统提示词
        """
        system_prompt = """你是 Radiant 项目的学术研究助手。你的职责是帮助研究人员进行学术研究、文献调研和论文撰写。

在回答问题时：
1. 引用相关的学术文献和研究成果
2. 提供基于最新研究的见解
3. 尽量使用知识图谱中的信息
4. 对不确定的信息进行声明
5. 建议用户查阅相关论文以获取更多信息"""

        if papers:
            paper_context = "\n".join([
                f"- {p.get('title', 'Unknown')} ({p.get('year', 'Unknown')})"
                for p in papers[:5]
            ])
            system_prompt += f"\n\n当前查询相关的论文：\n{paper_context}"

        return system_prompt

    def chat(
        self,
        user_id: str,
        session_id: str,
        message: str,
        search_graph: bool = True
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        处理用户消息并生成回复

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息
            search_graph: 是否搜索知识图谱

        Returns:
            Tuple: (AI回复, 引用列表)
        """
        # 保存用户消息
        self.save_conversation(user_id, session_id, "user", message)

        # 获取会话历史
        history = self.get_session_history(user_id, session_id, limit=10)

        # 从知识图谱搜索上下文
        papers = []
        references = []
        if search_graph:
            keywords = self.extract_keywords_from_message(message)
            papers, researchers = self.search_context_from_graph(keywords)
            references = [
                {
                    "type": "paper",
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "year": p.get("year")
                }
                for p in papers[:5]
            ]

        # 构建系统提示词
        system_prompt = self.build_system_prompt(papers)

        # 转换历史记录格式
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 添加历史对话（只保留最近的消息）
        for conv in history[-10:]:
            messages.append({
                "role": conv["role"],
                "content": conv["content"]
            })

        # 添加当前消息
        messages.append({"role": "user", "content": message})

        # 调用 LLM
        try:
            response_text = self.llm.chat_with_context(
                message,
                system_prompt=system_prompt,
                history=[conv for conv in history if conv["role"] in ["user", "assistant"]]
            )
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            response_text = "抱歉，生成回复时出现错误。请稍后重试。"

        # 保存 AI 回复
        self.save_conversation(
            user_id,
            session_id,
            "assistant",
            response_text,
            references=references if references else None
        )

        return response_text, references

    def stream_chat(
        self,
        user_id: str,
        session_id: str,
        message: str,
        search_graph: bool = True
    ):
        """
        流式处理用户消息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息
            search_graph: 是否搜索知识图谱
            
        Yields:
            str: 流式返回的文本片段
        """
        # 保存用户消息
        self.save_conversation(user_id, session_id, "user", message)

        # 获取会话历史
        history = self.get_session_history(user_id, session_id, limit=10)

        # 知识图谱搜索和 LLM 响应并行优化：
        # 对于流式响应，我们希望尽快开始生成。
        # 如果启用搜索，会增加延迟。
        # 优化策略：
        # 1. 如果不需要强一致的上下文，可以先不等待搜索结果？(当前逻辑是必须等待)
        # 2. 优化搜索逻辑，减少搜索范围或超时时间。
        # 3. 在前端实现“正在搜索...”的状态提示。
        
        # 目前主要延迟来自于：
        # 1. extract_keywords_from_message (LLM调用)
        # 2. search_context_from_graph (Neo4j查询)
        # 3. stream_chat (LLM生成)
        
        # 优化：不等待关键词提取的 LLM 调用，而是使用简单的规则提取或跳过提取直接搜索（如果不精确）
        # 或者：并行执行？Python GIL限制了多线程，但IO密集型可以。
        # 但为了保证上下文质量，我们暂时保持逻辑，但确保 LLM 调用本身不被不必要的参数拖慢。
        
        # 从知识图谱搜索上下文
        if search_graph:
            # 优化：简单关键词提取，避免一次 LLM 调用
            # 如果消息很短，直接用消息本身作为关键词
            if len(message) < 20:
                keywords = [message]
            else:
                keywords = self.extract_keywords_from_message(message)
                
            papers, _ = self.search_context_from_graph(keywords)
        else:
            papers = []

        # 构建系统提示词
        system_prompt = self.build_system_prompt(papers)

        # 转换历史记录格式
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 添加历史对话
        for conv in history[-10:]:
            messages.append({
                "role": conv["role"],
                "content": conv["content"]
            })

        # 添加当前消息
        messages.append({"role": "user", "content": message})

        # 流式调用 LLM
        full_response = ""
        try:
            for chunk in self.llm.stream_chat(messages):
                full_response += chunk
                yield chunk
        except Exception as e:
            logger.error(f"LLM 流式调用失败: {e}")
            yield "抱歉，生成回复时出现错误。"

        # 保存完整回复
        if full_response:
            self.save_conversation(user_id, session_id, "assistant", full_response)
