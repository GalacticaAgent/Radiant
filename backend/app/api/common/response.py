from typing import Any, Optional

from app.schemas.common import ApiResponse


def ok(data: Optional[Any] = None, msg: str = "ok") -> ApiResponse:
    return ApiResponse(code=0, msg=msg, data=data)


def fail(code: int, msg: str, data: Optional[Any] = None) -> ApiResponse:
    return ApiResponse(code=code, msg=msg, data=data)

