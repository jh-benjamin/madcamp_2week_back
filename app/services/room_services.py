from datetime import datetime
from fastapi import HTTPException
from db.database import execute_query
from schemas.rooms import RoomRequest, Item

async def create_room_service(room_data: RoomRequest):
    try:
        # 방 데이터 준비
        title = room_data.title
        host_uuid = room_data.host_uuid
        friend_uuids = room_data.friend_uuids  # 친구 UUID 리스트
        num_of_participants = len(friend_uuids) + 1  # 친구 수 + 호스트
        created_at = datetime.now()
        status = 1  # 진행 중

        # 방 생성 쿼리 실행
        room_query = """
        INSERT INTO rooms (title, hostUuid, numOfParticipants, createdAt, status)
        VALUES (%s, %s, %s, %s, %s)
        """
        room_id = await execute_query(room_query, [title, host_uuid, num_of_participants, created_at, status])

        # 친구 UUID 저장
        friend_query = """
        INSERT INTO room_participants (roomId, userUuid)
        VALUES (%s, %s)
        """
        for friend_uuid in friend_uuids:
            await execute_query(friend_query, [room_id, friend_uuid])

        # 영수증 데이터 저장
        item_query = """
        INSERT INTO room_items (roomId, menu, details, price)
        VALUES (%s, %s, %s, %s)
        """
        for item in room_data.items:
            await execute_query(item_query, [room_id, item.menu, item.details, item.price])

        return {
            "status": 201,
            "msg": "방이 성공적으로 생성되었습니다.",
            "data": {
                "roomId": room_id,
                "title": title,
                "hostUuid": host_uuid,
                "friendUuids": friend_uuids,
                "numOfParticipants": num_of_participants,
                "items": room_data.items,
                "totalPrice": room_data.total_price,
                "createdAt": created_at,
                "status": status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방 생성 중 오류 발생: {str(e)}")