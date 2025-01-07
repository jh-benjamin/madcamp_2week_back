from mysql.connector import Error
import pymysql
from datetime import datetime, timedelta
import uuid
import secrets
import hashlib
    
# DB 연결 설정
def get_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="p@ssword123",
            database="paycheck",
            charset="utf8mb4",          # UTF-8 지원
            cursorclass=pymysql.cursors.DictCursor  # DictCursor로 설정
        )
        return connection
    except pymysql.Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None
    
def update_user_item_check(receipt_item_id: int, user_uuid: str, checked: int):
    """
    userItemChecks 테이블의 checked 상태 업데이트
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            UPDATE userItemChecks
            SET checked = %s
            WHERE receiptItemId = %s AND userUuid = %s
        """
        print(f"Updating userItemChecks with receipt_item_id={receipt_item_id}, user_uuid={user_uuid}, checked={checked}")
        res = cursor.execute(query, (checked, receipt_item_id, user_uuid))
        connection.commit()
        print(res)
        return True  # 변경된 행 수가 0보다 큰지 확인

    except Exception as e:
        print(f"Error updating user item check: {e}")
        return False

    finally:
        cursor.close()
        connection.close()


def count_checked_users_by_receipt_item_id(receipt_item_id: int):
    """
    receiptItemId 별로 체크된 사용자 수를 반환하고,
    receiptItems 테이블의 numOfCheckedItems를 업데이트
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        count_query = """
            SELECT COUNT(*) AS check_count
            FROM userItemChecks
            WHERE receiptItemId = %s AND checked = TRUE
        """
        cursor.execute(count_query, (receipt_item_id,))
        result = cursor.fetchone()
        print(f"Result from count_query: {result}")
        check_count = result["check_count"] if result else 0
        
        # receiptItems 테이블의 numOfCheckedItems 업데이트
        update_query = """
            UPDATE receiptItems
            SET numOfCheckedItems = %s
            WHERE id = %s
        """
        cursor.execute(update_query, (check_count, receipt_item_id))
        connection.commit()

        return check_count

    except Exception as e:
        print(f"Error counting checked users for receiptItemId {receipt_item_id}: {e}")
        return 0

    finally:
        cursor.close()
        connection.close()


def get_receipt_items_by_room_id(room_id: int):
    """
    방 ID를 기반으로 receipts와 receiptItems 데이터를 조회
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # receipts 테이블에서 해당 방의 receipt ID를 조회
        query_receipt_id = """
            SELECT id
            FROM receipts
            WHERE roomId = %s
        """
        cursor.execute(query_receipt_id, (room_id,))
        receipt = cursor.fetchone()

        if not receipt:
            return []

        receipt_id = receipt["id"]

        # receiptItems 테이블에서 receipt ID에 해당하는 아이템 조회
        query_receipt_items = """
            SELECT id, itemName, details, price
            FROM receiptItems
            WHERE receiptId = %s
        """
        cursor.execute(query_receipt_items, (receipt_id,))
        receipt_items = cursor.fetchall()

        return [
            {
                "id": item["id"],
                "itemName": item["itemName"],
                "details": item["details"],
                "price": float(item["price"]),
            }
            for item in receipt_items
        ]

    except Exception as e:
        print(f"Error fetching receipt items for room_id {room_id}: {e}")
        return []

    finally:
        cursor.close()
        connection.close()

def get_rooms_by_user_uuid(user_uuid: str):
    """
    특정 사용자의 UUID를 기반으로 사용자가 속한 방 ID 리스트를 반환
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT DISTINCT roomId
            FROM roomParticipants
            WHERE userUuid = %s
        """
        cursor.execute(query, (user_uuid,))
        results = cursor.fetchall()

        # 결과에서 roomId 리스트 생성
        room_ids = [row["roomId"] for row in results]
        active_room_ids = filter_active_rooms(room_ids)

        return active_room_ids

    except Exception as e:
        print(f"Error fetching rooms for user_uuid {user_uuid}: {e}")
        return []

    finally:
        cursor.close()
        connection.close()

def filter_active_rooms(room_ids):
    """
    주어진 room_ids 리스트에서 status가 0인 방을 제외하고 반환
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # status가 1인 방만 선택
        query = """
            SELECT id
            FROM rooms
            WHERE id IN %s AND status = 1
        """
        # 튜플 형식으로 room_ids 전달
        cursor.execute(query, (tuple(room_ids),))
        results = cursor.fetchall()

        # 결과에서 방 ID만 추출
        active_room_ids = [row["id"] for row in results]

        return active_room_ids

    except Exception as e:
        print(f"Error filtering active rooms: {e}")
        return []

    finally:
        cursor.close()
        connection.close()

# 닉네임으로 사용자 조회
def get_user_by_name(name: str):
    connection = get_connection()
    cursor = connection.cursor()
    query = "SELECT uuid FROM users WHERE name = %s"
    cursor.execute(query, (name,))
    uuid = cursor.fetchone()
    cursor.close()
    connection.close()
    # 사용자 없을 경우 None 반환
    if not uuid:
        return None
    
    return uuid

# 새로운 사용자 생성
def create_user(name: str):
    connection = get_connection()
    cursor = connection.cursor()

    # UUID 생성
    user_uuid = str(uuid.uuid4())

    # INSERT 쿼리
    query = "INSERT INTO users (uuid, name) VALUES (%s, %s)"
    cursor.execute(query, (user_uuid, name))
    connection.commit()

    cursor.close()
    connection.close()

    return user_uuid  # 새로 생성된 사용자 UUID 반환

# 토큰 저장
def create_user_token(user_uuid: str):
    connection = get_connection()
    cursor = connection.cursor()

    # 발급 시간
    issued_at = datetime.now()

    # Access Token 및 Refresh Token 만료 시간 설정
    expires_at = issued_at + timedelta(days=60)  # Access Token 만료: 60일 후

     # 무작위 토큰 생성 (256비트)
    random_string = secrets.token_hex(32)  # 64자리의 무작위 문자열
    token_value = hashlib.sha256(random_string.encode()).hexdigest()  # SHA256 해시 생성

    # INSERT 쿼리
    query = """
        INSERT INTO tokens (userUuid, tokenValue, issuedAt, expiresAt)
        VALUES (%s, %s, %s, %s)
    """
    # tokenValue에 Access Token만 저장 (Refresh Token은 별도로 관리 가능)
    cursor.execute(query, (user_uuid, token_value, issued_at, expires_at))
    connection.commit()

    cursor.close()
    connection.close()

    return token_value

# db/database.py 파일에 execute_query가 정의되어 있어야 합니다.
def execute_query(query: str, params: tuple = ()):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(query, params)
    cursor.fetchall()
    
    result = cursor.lastrowid

    cursor.close()
    connection.close()
    return result