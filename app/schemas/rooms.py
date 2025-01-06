from pydantic import BaseModel
from typing import List

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