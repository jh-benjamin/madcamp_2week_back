from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.room_services import create_room_service
from schemas.rooms import RoomRequest, UpdateRoomStatusRequest
from schemas.response import ResponseSchema
from db.database import get_user_by_name, get_rooms_by_user_uuid
from db.room import get_hosted_rooms_by_user_uuid, get_participating_rooms_by_user_uuid, get_all_participating_rooms_by_user_uuid, update_room_status_in_db

# 라우터 초기화
router = APIRouter()

@router.post("/updateRoomStatus", response_model=ResponseSchema)
async def update_room_status(request: UpdateRoomStatusRequest):
    """
    특정 roomId의 status 값을 업데이트하는 API
    """
    try:
        # DB 업데이트 함수 호출
        success = update_room_status_in_db(request.roomId, request.status)

        if not success:
            raise HTTPException(status_code=404, detail="해당 roomId를 찾을 수 없습니다.")

        return ResponseSchema(
            status=200,
            msg=f"roomId {request.roomId}의 상태가 {request.status}로 업데이트되었습니다.",
            data=None
        )

    except HTTPException as e:
        # HTTPException은 그대로 반환
        raise e

    except Exception as e:
        # 기타 예외는 500 에러로 처리
        return ResponseSchema(
            status=500,
            msg="상태 업데이트 중 오류 발생",
            data=str(e)
        )

@router.get("/getRoomsByStatus/{user_uuid}", response_model=ResponseSchema)
async def get_user_rooms_by_status(user_uuid: str):
    """
    주어진 user_uuid에 대해, 방을 status 값에 따라 정리해서 반환
    status == 1: 정산 시작 전
    status == 2: 정산 시작 후
    """
    try:
        # DB에서 사용자가 참여 중인 모든 방 가져오기
        participating_rooms = get_all_participating_rooms_by_user_uuid(user_uuid)

        # print(f"participating_rooms:{participating_rooms}")

        # 방을 status에 따라 분류
        rooms_by_status = {"beforeSettlement": [], "afterSettlement": []}
        for room in participating_rooms:
            if room["status"] == 1:
                rooms_by_status["beforeSettlement"].append(room["title"])
            elif room["status"] == 2:
                rooms_by_status["afterSettlement"].append(room["title"])

        # print(f"rooms_by_status:{rooms_by_status}")

        return ResponseSchema(
            status=200,
            msg="방 정보 검색 및 분류 성공",
            data=rooms_by_status
        )

    except HTTPException as e:
        return ResponseSchema(
            status=500,
            msg="방 정보 검색 중 서버 내부 오류",
            data={"error": str(e)}
        )

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="방 정보 검색 중 기타 오류",
            data={"error": str(e)}
        )

@router.get("/getRooms/{user_uuid}", response_model=ResponseSchema)
async def get_user_rooms(user_uuid: str):
    """
    주어진 user_uuid에 대해, 호스트인 방의 title과 참여 중인 방의 title 반환 API
    """
    try:
        # DB에서 해당 사용자가 호스트인 방 가져오기
        hosted_rooms = get_hosted_rooms_by_user_uuid(user_uuid)

        # DB에서 해당 사용자가 참여 중인 방(호스트 제외) 가져오기
        participating_rooms = get_participating_rooms_by_user_uuid(user_uuid)

        return ResponseSchema(
            status=200,
            msg="방 정보 검색 성공",
            data={
                "hostedRooms": [room["title"] for room in hosted_rooms],
                "participatingRooms": [room["title"] for room in participating_rooms],
            }
        )

    except HTTPException as e:
        return ResponseSchema(
            status=500,
            msg="방 정보 검색 중 서버 내부 오류",
            data={"error": str(e)}
        )

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="방 정보 검색 중 기타 오류",
            data={"error": str(e)}
        )

@router.get("/findRoomId/{user_uuid}", response_model=ResponseSchema)
async def find_room_id(user_uuid: str):
    """
    특정 사용자가 속해 있는 방의 ID 리스트 반환 API
    """
    try:
        # database.py에서 get_rooms_by_user_uuid 함수 호출
        room_ids = get_rooms_by_user_uuid(user_uuid)

        if not room_ids:
            return ResponseSchema(
                status=404,
                msg="사용자가 속한 방이 없습니다.",
                data=None
            )

        return ResponseSchema(
            status=200,
            msg="사용자가 속한 방 ID 검색 성공",
            data={"roomIds": room_ids}
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="방 ID 검색 중 서버 내부 오류",
            data={"error": str(e)}
        )

@router.get("/findUuid/{name}", response_model=ResponseSchema)
async def find_friend_uuid(name: str):
    """
    특정 이름을 가진 사용자의 UUID 반환 API
    """
    try:
        # database.py의 get_user_by_name 함수 호출
        uuid = get_user_by_name(name)

        if not uuid:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        return ResponseSchema(
            status=200,
            msg="사용자 검색 성공",
            data={"uuid": uuid}
        )

    except HTTPException as e:
        return e

    except Exception as e:
        return e

@router.post("/createRoom", response_model=ResponseSchema)
async def create_room(room_data: RoomRequest):
    """
    방 생성 API
    """
    try:
        # 서비스 레이어 호출
        response = await create_room_service(room_data)
        print(f"response:{response}")
        return response

    except HTTPException as e:
        return ResponseSchema(
            status=500,
            msg="방 생성 중 FastAPI 오류",
            data={"error": f"방 생성 중 오류 발생: {str(e)}"}
        )

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="방 생성 중 서버 내부 오류",
            data={"error": f"방 생성 중 오류 발생: {str(e)}"}
        )
