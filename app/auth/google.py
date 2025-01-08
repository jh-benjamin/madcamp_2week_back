import requests
from fastapi import HTTPException
import os
from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")

def verify_google_id_token(id_token_str: str):
    try:
        # 구글의 공개 키로 ID 토큰 검증
        user_info = id_token.verify_oauth2_token(
            id_token_str,
            requests.Request(),
            "568897327149-7fnbjul15in412m1cda9dqmsjncc2ubc.apps.googleusercontent.com"  # OAuth 2.0 클라이언트 ID
        )
        
        # 유효한 토큰이면 user_info 반환
        return user_info
    except ValueError:
        # 유효하지 않은 토큰일 경우 예외 처리
        raise HTTPException(status_code=401, detail="Invalid Google ID Token")

# Google Identity Platform API 호출 함수
def get_google_user_info(access_token: str):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={GOOGLE_KEY}"  # Google Identity Platform API 엔드포인트
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "idToken": access_token  # 액세스 토큰을 ID 토큰으로 사용
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        user_info = response.json()

        # 이름 가져오기
        name = user_info.get("users", [{}])[0].get("displayName", None)

        return name
    else:
        print(response)
        raise HTTPException(status_code=401, detail="Invalid Google access token")