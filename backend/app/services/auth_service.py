"""
用户认证服务
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token
)


class AuthService:
    """用户认证服务类"""

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            Optional[User]: 用户对象，不存在返回 None
        """
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            db: 数据库会话
            email: 邮箱

        Returns:
            Optional[User]: 用户对象，不存在返回 None
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        根据ID获取用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象，不存在返回 None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """
        创建新用户

        Args:
            db: 数据库会话
            user_create: 用户创建数据

        Returns:
            User: 创建的用户对象

        Raises:
            HTTPException: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        if AuthService.get_user_by_username(db, user_create.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        if AuthService.get_user_by_email(db, user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
        """
        验证用户身份

        Args:
            db: 数据库会话
            username_or_email: 用户名或邮箱
            password: 密码

        Returns:
            Optional[User]: 验证成功返回用户对象，否则返回 None
        """
        # 尝试通过用户名查找
        user = AuthService.get_user_by_username(db, username_or_email)

        # 如果用户名找不到，尝试通过邮箱查找
        if not user:
            user = AuthService.get_user_by_email(db, username_or_email)

        # 用户不存在或密码错误
        if not user or not verify_password(password, user.hashed_password):
            return None

        # 检查用户是否激活
        if not user.is_active:
            return None

        return user

    @staticmethod
    def create_user_token(user: User) -> Token:
        """
        为用户创建 Token

        Args:
            user: 用户对象

        Returns:
            Token: 包含 access_token 和 refresh_token
        """
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )
