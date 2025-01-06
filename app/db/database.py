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
    
# 닉네임으로 사용자 조회
def get_user_by_name(name: str):
    connection = get_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM users WHERE name = %s"
    cursor.execute(query, (name,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

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