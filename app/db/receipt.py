from db.database import get_connection

def get_receipt_items_by_receipt_id(receipt_id: int):
    query = """
        SELECT itemName, price
        FROM receiptItems
        WHERE receiptId = %s
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, (receipt_id,))
    items = cursor.fetchall()
    cursor.close()
    connection.close()
    return {item["itemName"]: item for item in items}

def calculate_user_totals(user_checks, item_check_counts, receipt_items):
    user_totals = {}
    for user_uuid, data in user_checks.items():
        total = 0
        for item_name in data["items"]:
            price = receipt_items[item_name]["price"]
            participants = item_check_counts[item_name]
            total += price / participants
        user_totals[user_uuid] = {"name": data["name"], "total": round(total, 2)}
    return user_totals

def calculate_user_checks_and_item_counts(receipt_id: int):
    query = """
        SELECT u.userUuid, u.name, ri.itemName, uc.checked
        FROM userItemChecks uc
        JOIN users u ON uc.userUuid = u.uuid
        JOIN receiptItems ri ON uc.receiptItemId = ri.id
        WHERE ri.receiptId = %s
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, (receipt_id,))
    checks = cursor.fetchall()
    cursor.close()
    connection.close()

    user_checks = {}
    item_check_counts = {}

    for check in checks:
        user_uuid = check["userUuid"]
        item_name = check["itemName"]
        checked = check["checked"]

        if user_uuid not in user_checks:
            user_checks[user_uuid] = {"name": check["name"], "items": []}
        if checked:
            user_checks[user_uuid]["items"].append(item_name)
            item_check_counts[item_name] = item_check_counts.get(item_name, 0) + 1

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
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, (receipt_id,))
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return users

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