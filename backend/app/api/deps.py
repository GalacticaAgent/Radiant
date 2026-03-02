"""
API 依赖注入函数
"""

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.db.neo4j import get_neo4j
from app.core.security import decode_token
from app.services.auth_service import AuthService
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.models.user import User

# HTTP Bearer Token 认证
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)  # 不自动抛出错误


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    Args:
        credentials: HTTP Bearer Token
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: Token 无效或用户不存在
    """
    token = credentials.credentials

    # 解码 Token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 Token 类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库获取用户
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


def get_current_user_from_query(
    token: str = Query(None, description="认证令牌"),
    credentials: HTTPAuthorizationCredentials = Depends(optional_security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户（支持 Header 和 Query 参数）

    用于 SSE 端点，因为 EventSource 不支持自定义 Header

    Args:
        token: 查询参数中的认证令牌（可选）
        credentials: HTTP Bearer Token（可选）
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: Token 无效或用户不存在
    """
    # 优先使用 Header 中的 token，其次使用查询参数
    auth_token = None
    if credentials and credentials.credentials:
        auth_token = credentials.credentials
    elif token:
        auth_token = token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 解码 Token
    payload = decode_token(auth_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 Token 类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库获取用户
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前超级管理员用户

    Args:
        current_user: 当前用户

    Returns:
        User: 超级管理员用户

    Raises:
        HTTPException: 用户不是超级管理员
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user


def get_llm_service() -> LLMService:
    """获取 LLM 服务实例"""
    return LLMService()


def get_graph_service(neo4j_conn=Depends(get_neo4j)):
    """获取知识图谱服务实例"""
    return GraphService(neo4j_conn)
