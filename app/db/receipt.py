from db.database import get_connection

def get_user_item_check_status(receipt_item_id: int, user_uuid: str):
    """
    특정 receiptItemId와 userUuid를 기반으로 사용자가 체크했는지 여부 반환
    """
    query = """
        SELECT checked
        FROM userItemChecks
        WHERE receiptItemId = %s AND userUuid = %s
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()  # dictionary=True로 결과를 딕셔너리 형태로 반환
        cursor.execute(query, (receipt_item_id, user_uuid))
        result = cursor.fetchone()
        return result["checked"] if result else False
    except Exception as e:
        print(f"Error in get_user_item_check_status: {e}")
    finally:
        cursor.close()
        connection.close()

def get_receipt_items_by_room_id(room_id: int):
    """
    특정 roomId에 해당하는 receiptItems 가져오기
    """
    query = """
        SELECT ri.id, ri.itemName, ri.price
        FROM receiptItems ri
        JOIN receipts r ON ri.receiptId = r.id
        WHERE r.roomId = %s
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (room_id,))
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"Error in get_receipt_items_by_room_id: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def update_is_paid(room_id: int, user_uuid: str, is_paid: int):
    """
    roomId와 userUuid를 기반으로 roomParticipants의 isPaid 값을 업데이트
    """
    query = """
        UPDATE roomParticipants
        SET isPaid = %s
        WHERE roomId = %s AND userUuid = %s
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        # 업데이트 실행
        cursor.execute(query, (is_paid, room_id, user_uuid))
        connection.commit()
        cursor.close()
        connection.close()
        return {"status": "success", "msg": f"roomId {room_id}, userUuid {user_uuid}의 isPaid 값을 {is_paid}로 업데이트했습니다."}
    except Exception as e:
        cursor.close()
        connection.close()
        print(f"Error updating isPaid: {e}")
        return {"status": "error", "msg": "isPaid 값을 업데이트하는 중 오류가 발생했습니다.", "error": str(e)}

def get_item_check_counts(receipt_id: int):
    """
    receiptId를 기반으로 각 receiptItem에 대해 몇 명이나 체크했는지 반환
    """
    query = """
        SELECT ri.id AS itemId, ri.itemName, COUNT(uc.userUuid) AS checkCount
        FROM receiptItems ri
        LEFT JOIN userItemChecks uc ON ri.id = uc.receiptItemId AND uc.checked = 1
        WHERE ri.receiptId = %s
        GROUP BY ri.id, ri.itemName
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, (receipt_id,))
        items = cursor.fetchall()
        cursor.close()
        connection.close()

        # 결과를 딕셔너리로 변환
        return {item["itemName"]: item["checkCount"] for item in items}
    
    except Exception as e:
        cursor.close()
        connection.close()
        print(f"Error fetching item check counts: {e}")
        return None

def get_receipt_items_by_receipt_id(receipt_id: int):
    query = """
        SELECT itemName, price
        FROM receiptItems
        WHERE receiptId = %s
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, (receipt_id,))
    items = cursor.fetchall()
    cursor.close()
    connection.close()
    return {item["itemName"]: item for item in items}

def calculate_user_totals(user_checks, item_check_counts, receipt_items):
    user_totals = {}
    for user_uuid, data in user_checks.items():
        total = 0
        for item in data["items"]:
            item_name = item["name"]
            price = receipt_items[item_name]["price"]
            participants = item_check_counts.get(item_name, 1)  # 기본값 1
            total += price / participants
        user_totals[user_uuid] = {"name": data["name"], "total": round(total, 2)}
    return user_totals

def calculate_user_checks_and_item_counts(receipt_id: int):
    """
    receiptId를 기반으로 사용자별 체크 정보와 메뉴별 체크 인원수 반환
    """
    # 메뉴별 체크된 사용자 수 가져오기
    item_check_counts = get_item_check_counts(receipt_id)

    query = """
        SELECT u.uuid, u.name, ri.itemName, ri.price, uc.checked
        FROM userItemChecks uc
        JOIN users u ON uc.userUuid = u.uuid
        JOIN receiptItems ri ON uc.receiptItemId = ri.id
        WHERE ri.receiptId = %s
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, (receipt_id,))
    checks = cursor.fetchall()
    cursor.close()
    connection.close()

    user_checks = {}

    # 사용자 체크 데이터 생성
    for check in checks:
        user_uuid = check["uuid"]
        item_name = check["itemName"]
        item_price = check["price"]
        checked = check["checked"]

        # 사용자별 체크 정보 초기화
        if user_uuid not in user_checks:
            user_checks[user_uuid] = {"name": check["name"], "items": []}

        if checked:
            # n빵된 가격 계산
            participants = item_check_counts.get(item_name, 1)  # 기본값 1
            price_per_person = round(item_price / participants, 2)

            # 사용자별 체크 정보 추가
            user_checks[user_uuid]["items"].append({
                "name": item_name,
                "price": price_per_person  # n빵된 가격 저장
            })

    return user_checks, item_check_counts

def get_users_in_receipt(receipt_id: int):
    query = """
        SELECT rp.userUuid, u.name
        FROM roomParticipants rp
        JOIN receipts r ON rp.roomId = r.roomId
        JOIN users u ON rp.userUuid = u.uuid
        WHERE r.id = %s
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, (receipt_id,))
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return users