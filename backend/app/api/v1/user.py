"""
用户 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(tags=["users"])


@router.get("/profile", response_model=UserResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户资料
    """
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户资料

    - **username**: 用户名（可选）
    - **email**: 邮箱（可选）
    """
    # 检查用户名是否已被使用（如果要更新的话）
    if user_update.username and user_update.username != current_user.username:
        existing = db.query(User).filter(User.username == user_update.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        current_user.username = user_update.username

    # 检查邮箱是否已被使用
    if user_update.email and user_update.email != current_user.email:
        existing = db.query(User).filter(User.email == user_update.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        current_user.email = user_update.email

    db.commit()
    db.refresh(current_user)

    return UserResponse.from_orm(current_user)
