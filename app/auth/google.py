import requests
from fastapi import HTTPException
import os

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")

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