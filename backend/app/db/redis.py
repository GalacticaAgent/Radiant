"""
Redis 连接和缓存管理
"""

import json
from typing import Any, Optional
import redis
from app.core.config import settings


class RedisClient:
    """Redis 客户端封装类"""

    def __init__(self, url: str):
        """
        初始化 Redis 连接

        Args:
            url: Redis 连接 URL
        """
        self._url = url
        self._client = redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        """
        获取值

        Args:
            key: 键

        Returns:
            Optional[str]: 值，不存在返回 None
        """
        try:
            return self._client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        设置值

        Args:
            key: 键
            value: 值
            ex: 过期时间（秒）

        Returns:
            bool: 是否成功
        """
        try:
            return bool(self._client.set(key, value, ex=ex))
        except Exception:
            return False

    def delete(self, key: str) -> int:
        """
        删除键

        Args:
            key: 键

        Returns:
            int: 删除的键数量
        """
        try:
            return int(self._client.delete(key))
        except Exception:
            return 0

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键

        Returns:
            bool: 是否存在
        """
        try:
            return self._client.exists(key) > 0
        except Exception:
            return False

    def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """
        设置 JSON 值

        Args:
            key: 键
            value: Python 对象（会被序列化为 JSON）
            ex: 过期时间（秒）

        Returns:
            bool: 是否成功
        """
        json_str = json.dumps(value, ensure_ascii=False)
        return self.set(key, json_str, ex=ex)

    def get_json(self, key: str) -> Optional[Any]:
        """
        获取 JSON 值

        Args:
            key: 键

        Returns:
            Optional[Any]: Python 对象，不存在返回 None
        """
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def ping(self) -> bool:
        """
        检查连接是否正常

        Returns:
            bool: 连接是否正常
        """
        try:
            return bool(self._client.ping())
        except redis.exceptions.AuthenticationError:
            alt = self._url
            if ":6379/" in alt:
                alt = alt.replace(":6379/", ":6380/")
            elif "localhost:6379" in alt:
                alt = alt.replace("localhost:6379", "localhost:6380")
            elif "127.0.0.1:6379" in alt:
                alt = alt.replace("127.0.0.1:6379", "127.0.0.1:6380")
            if alt != self._url:
                try:
                    client = redis.from_url(alt, decode_responses=True)
                    if client.ping():
                        self._client = client
                        self._url = alt
                        return True
                except Exception:
                    return False
            return False
        except Exception:
            return False


# 创建全局 Redis 客户端实例
redis_client = RedisClient(settings.REDIS_URL)


def get_redis() -> RedisClient:
    """
    获取 Redis 客户端的依赖函数
    用于 FastAPI 的依赖注入

    Returns:
        RedisClient: Redis 客户端实例
    """
    return redis_client
