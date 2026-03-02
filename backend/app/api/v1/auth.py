"""
用户认证 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User
from app.core.security import decode_token, create_access_token
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求"""
    username_or_email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    - **username**: 用户名（3-50个字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少8个字符）
    """
    # 创建用户
    user = AuthService.create_user(db, user_create)

    # 生成 Token
    token = AuthService.create_user_token(user)

    return token


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录

    - **username_or_email**: 用户名或邮箱
    - **password**: 密码

    返回 access_token 和 refresh_token
    """
    # 验证用户身份
    user = AuthService.authenticate_user(
        db,
        login_data.username_or_email,
        login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成 Token
    token = AuthService.create_user_token(user)

    return token


@router.post("/refresh", response_model=dict)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    刷新 Access Token

    - **refresh_token**: Refresh Token

    返回新的 access_token
    """
    # 解码 Refresh Token
    refresh_token = request.refresh_token
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Refresh Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 Token 类型
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Refresh Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户是否存在
    user = AuthService.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成新的 Access Token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息

    需要在请求头中携带 Bearer Token:
    ```
    Authorization: Bearer {access_token}
    ```
    """
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出

    （当前为前端处理，删除本地 Token）
    """
    return {"message": "登出成功"}
