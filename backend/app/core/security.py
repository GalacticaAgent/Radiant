"""
安全模块 - JWT Token 和密码处理
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
import base64
from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码是否匹配
    """
    # 将长密码通过 SHA256 哈希，确保不超过 72 字节限制
    processed_password = _process_password(plain_password)
    return pwd_context.verify(processed_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        str: 哈希密码
    """
    # 将长密码通过 SHA256 哈希，确保不超过 72 字节限制
    processed_password = _process_password(password)
    return pwd_context.hash(processed_password)


def _process_password(password: str) -> str:
    """
    处理密码，确保不超过 bcrypt 的 72 字节限制

    使用 SHA256 哈希长密码，将输出编码为 base64，确保长度可控

    Args:
        password: 原始密码

    Returns:
        str: 处理后的密码（< 72 字节）
    """
    if len(password.encode('utf-8')) <= 72:
        return password

    # 对长密码进行 SHA256 哈希
    hash_obj = hashlib.sha256(password.encode('utf-8'))
    # 编码为 base64 确保是可打印的 ASCII 字符
    hashed = base64.b64encode(hash_obj.digest()).decode('utf-8')
    return hashed


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 Access Token

    Args:
        data: 要编码的数据（通常包含 sub: user_id）
        expires_delta: 过期时间增量

    Returns:
        str: JWT Token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    创建 Refresh Token

    Args:
        data: 要编码的数据

    Returns:
        str: Refresh Token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # Refresh Token 有效期 30 天
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 Token

    Args:
        token: JWT Token

    Returns:
        Dict: Token 中的数据，解码失败返回 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def validate_token_type(token: str, expected_type: str) -> bool:
    """
    验证 Token 类型

    Args:
        token: JWT Token
        expected_type: 期望的类型 (access/refresh)

    Returns:
        bool: 类型是否匹配
    """
    payload = decode_token(token)
    if not payload:
        return False
    return payload.get("type") == expected_type
