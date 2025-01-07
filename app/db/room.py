from db.database import get_connection
from typing import List, Dict

def get_hosted_rooms_by_user_uuid(user_uuid: str):
    """
    사용자가 호스트인 방을 가져오는 함수
    """
    query = """
        SELECT title 
        FROM rooms
        WHERE hostUuid = %s
    """
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(query, (user_uuid,))
        temp = cursor.fetchall()

    connection.close()

    return temp

def get_participating_rooms_by_user_uuid(user_uuid: str):
    """
    사용자가 참여 중인 방(호스트 제외)을 가져오는 함수
    """
    query = """
        SELECT r.title 
        FROM rooms r
        JOIN roomParticipants rp ON r.id = rp.roomId
        WHERE rp.userUuid = %s AND r.hostUuid != %s
    """
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(query, (user_uuid, user_uuid))
        temp = cursor.fetchall()
    connection.close()

    return temp

def get_all_participating_rooms_by_user_uuid(user_uuid: str) -> List[Dict]:
    """
    사용자의 UUID를 기반으로, 사용자가 참여 중인 모든 방을 가져오는 함수.
    """
    try:
        # DB 연결
        connection = get_connection()
        cursor = connection.cursor()

        # 사용자가 참여 중인 방 가져오는 쿼리
        query = """
        SELECT r.id, r.title, r.status
        FROM rooms r
        JOIN roomParticipants rp ON r.id = rp.roomId
        WHERE rp.userUuid = %s
        """
        cursor.execute(query, (user_uuid,))

        # 결과 가져오기
        result = cursor.fetchall()

        # 결과를 리스트로 정리
        rooms = [
            {"room_id": row[0], "title": row[1], "status": row[2]}
            for row in result
        ]

        return rooms

    except Exception as e:
        raise Exception(f"DB에서 참여 중인 방을 가져오는 중 오류 발생: {e}")
    
    finally:
        # DB 연결 종료
        cursor.close()
        connection.close()