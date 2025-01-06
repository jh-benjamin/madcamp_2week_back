import requests
from schemas.response import ResponseSchema
from fastapi import HTTPException

# 카카오 API 설정
CLIENT_ID = "10222c717d82e4a5bb07c9d91055c3f5"
REDIRECT_URI = "http://172.10.7.18:8000/auth/kakao/callback"

# 1. 카카오 로그인 URL 생성
def get_kakao_login_url():
    login_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
    )
    return login_url

# 2. 카카오 액세스 토큰 발급
def get_kakao_access_token(code: str):
    url = "https://kauth.kakao.com/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        print(f"카카오 요청 실패: {response.text}")
        raise HTTPException(status_code=400, detail="카카오 액세스 토큰 요청 실패")

    token_data = response.json()
    return token_data

def get_kakao_user_info(access_token: str):
    """
    카카오 서버에서 사용자 정보를 가져오는 함수
    """
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Authorization": f"Bearer {access_token}"  # Bearer 인증 헤더
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"카카오 사용자 정보 요청 실패: {response.text}"
        )

    user_data = response.json()

    # kakao_account.profile.nickname에서 이름 가져오기
    kakao_account = user_data.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    nickname = profile.get("nickname")  # 닉네임 가져오기
    
    if not nickname:
        raise HTTPException(
            status_code=400,
            detail="사용자의 이름(닉네임)을 가져올 수 없습니다."
        )

    return name