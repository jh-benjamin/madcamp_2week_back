from typing import Any
from pydantic import BaseModel

class ResponseSchema(BaseModel):
    status: int  # 상태 코드
    msg: str  # 메시지
    data: Any  # 응답 데이터