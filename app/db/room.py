from db.database import get_connection

def update_room_status_in_db(room_id: int, status: int):
    """
    DB에서 특정 roomId의 status 값을 업데이트하는 함수
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        # SQL 쿼리 작성
        update_query = """
            UPDATE rooms
            SET status = %s
            WHERE id = %s
        """
        cursor.execute(update_query, (status, room_id))
        connection.commit()

        # 업데이트 성공 여부 확인
        if cursor.rowcount == 0:
            return False  # 해당 roomId가 없음을 의미

        return True  # 업데이트 성공

    except Exception as e:
        raise e  # 예외를 라우터로 전달

    finally:
        # 연결 닫기
        cursor.close()
        connection.close()

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

def get_all_participating_rooms_by_user_uuid(user_uuid: str):
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

        return result

    except Exception as e:
        raise Exception(f"DB에서 참여 중인 방을 가져오는 중 오류 발생: {e}")
    
    finally:
        # DB 연결 종료
        cursor.close()
        connection.close()