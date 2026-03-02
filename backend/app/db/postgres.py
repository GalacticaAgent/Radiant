"""
PostgreSQL 数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.POSTGRES_URI,
    connect_args={"connect_timeout": 3},
    pool_pre_ping=True,  # 连接池预ping，自动处理断开的连接
    pool_size=10,  # 连接池大小
    max_overflow=20  # 最大溢出连接数
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 类，所有模型都继承这个类
Base = declarative_base()


def get_db() -> Session:
    """
    获取数据库会话的依赖函数
    用于 FastAPI 的依赖注入

    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表（仅用于开发环境，生产环境应使用 Alembic）
    """
    from app.models import user  # noqa
    Base.metadata.create_all(bind=engine)
