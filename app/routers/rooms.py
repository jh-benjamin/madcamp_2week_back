from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.room_services import create_room_service
from schemas.rooms import RoomRequest, Item
from schemas.response import ResponseSchema

# 라우터 초기화
router = APIRouter()

@router.post("/create-room", response_model=ResponseSchema)
async def create_room(room_data: RoomRequest):
    """
    방 생성 API
    """
    try:
        # 서비스 레이어 호출
        response = await create_room_service(room_data)
        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="방 생성 중 서버 내부 오류",
            data={"error": f"방 생성 중 오류 발생: {str(e)}"}
        )
