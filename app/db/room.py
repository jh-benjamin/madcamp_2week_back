from db.database import get_connection

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