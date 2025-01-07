from pydantic import BaseModel
from typing import List  # List를 올바르게 임포트

# POST 요청으로 받을 데이터 스키마 정의
class CheckUpdate(BaseModel):
    receiptItemId: int
    checked: bool

class UpdateCheckRequest(BaseModel):
    userUuid: str
    updates: List[CheckUpdate]  # 여러 항목 업데이트를 처리