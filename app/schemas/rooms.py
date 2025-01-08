from pydantic import BaseModel
from typing import List

# 출력 모델 정의
class ParticipantDetails(BaseModel):
    name: str
    amountOfMoney: float
    isPaid: bool

class RoomParticipantsResponse(BaseModel):
    status: int
    msg: str
    data: List[ParticipantDetails]

class Item(BaseModel):
    menu: str
    details: str
    price: str

class RoomRequest(BaseModel):
    title: str
    host_uuid: str
    friend_uuids: List[str]  # 친구 UUID 리스트
    items: List[Item]
    total_price: str

class UpdateRoomStatusRequest(BaseModel):
    roomId: int
    status: int