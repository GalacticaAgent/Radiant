from typing import Any, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: Optional[Any] = None

