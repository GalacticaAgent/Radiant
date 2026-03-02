"""
数据库初始化脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres import Base, engine
from app.db.neo4j import neo4j_conn
from app.db.redis import redis_client
from app.core.config import settings
from app.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_postgres():
    """初始化 PostgreSQL 数据库"""
    logger.info("初始化 PostgreSQL 数据库...")
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("✅ PostgreSQL 表创建成功")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL 初始化失败: {e}")
        return False


def verify_neo4j():
    """验证 Neo4j 连接"""
    logger.info("验证 Neo4j 连接...")
    try:
        if neo4j_conn.verify_connectivity():
            logger.info("✅ Neo4j 连接成功")
            return True
        else:
            logger.error("❌ Neo4j 连接失败")
            return False
    except Exception as e:
        logger.error(f"❌ Neo4j 连接错误: {e}")
        return False


def verify_redis():
    """验证 Redis 连接"""
    logger.info("验证 Redis 连接...")
    try:
        if redis_client.ping():
            logger.info("✅ Redis 连接成功")
            return True
        else:
            logger.warning("⚠️  Redis 连接失败 (可选服务，将跳过)")
            logger.info("✅ Redis 验证跳过 (缓存功能将不可用)")
            return True  # Return True to allow initialization to continue
    except Exception as e:
        logger.warning(f"⚠️  Redis 连接错误 (可选服务，将跳过): {e}")
        logger.info("✅ Redis 验证跳过 (缓存功能将不可用)")
        return True  # Return True to allow initialization to continue


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Radiant 后端数据库初始化")
    logger.info("=" * 60)
    logger.info("")

    results = {
        "PostgreSQL": init_postgres(),
        "Neo4j": verify_neo4j(),
        "Redis": verify_redis()
    }

    logger.info("")
    logger.info("=" * 60)
    logger.info("初始化结果汇总")
    logger.info("=" * 60)

    all_success = all(results.values())

    for db, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"{db:20s}: {status}")

    logger.info("")

    if all_success:
        logger.info("🎉 所有数据库初始化成功！")
        return 0
    else:
        logger.error("⚠️ 部分数据库初始化失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
