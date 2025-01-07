import pymysql

def get_connection():
    """
    데이터베이스 연결을 생성하는 함수
    """
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
        for item_name in data["items"]:
            price = receipt_items[item_name]["price"]
            participants = item_check_counts[item_name]
            total += price / participants
        user_totals[user_uuid] = {"name": data["name"], "total": round(total, 2)}
    return user_totals

def calculate_user_checks_and_item_counts(receipt_id: int):
    query = """
        SELECT u.uuid, u.name, ri.itemName, uc.checked
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
    cursor = connection.cursor()
    cursor.execute(query, (receipt_id,))
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return users