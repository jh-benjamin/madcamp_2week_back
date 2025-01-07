from datetime import datetime
from fastapi import HTTPException
from db.database import get_connection
from schemas.rooms import RoomRequest, Item

async def create_room_service(room_data: RoomRequest):
    try:
        connection = get_connection()
        cursor = connection.cursor()

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
        cursor.execute(room_query, [title, host_uuid, num_of_participants, created_at, status])
        room_id = cursor.lastrowid


        # 친구 UUID 저장
        participant_query = """
        INSERT INTO roomParticipants (roomId, userUuid, amountOfMoney, isPaid)
        VALUES (%s, %s, %s, %s)
        """

        # 호스트 추가
        cursor.execute(participant_query, [room_id, host_uuid, 0, 0])

        for friend_uuid in friend_uuids:
            cursor.execute(participant_query, [room_id, friend_uuid, 0, 0])

        recipt_query = """
        INSERT INTO receipts (roomId) VALUES (%s)
        """
        cursor.execute(recipt_query, [room_id])
        receiptId = cursor.lastrowid
        # 영수증 데이터 저장
        item_query = """
        INSERT INTO receiptItems (receiptId, itemName, numOfCheckedItems, details, price)
        VALUES (%s, %s, %s, %s, %s)
        """
        user_item_checks_query = """
        INSERT INTO userItemChecks (receiptItemId, userUuid, checked)
        VALUES (%s, %s, %s)
        """
        for item in room_data.items:
            cursor.execute(item_query, [receiptId, item.menu, 0, item.details, item.price])
            receipt_item_id = cursor.lastrowid  # 방금 추가된 receiptItem의 ID 가져오기

            # userItemChecks에 각 사용자 추가
            for user_uuid in [host_uuid] + friend_uuids:  # 호스트와 친구들 포함
                cursor.execute(user_item_checks_query, [receipt_item_id, user_uuid, False])
        # 트랜잭션 커밋
        connection.commit()

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
    finally:
        cursor.close()
        connection.close()