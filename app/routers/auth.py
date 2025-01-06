from fastapi import APIRouter
from schemas.response import ResponseSchema
from auth.kakao import get_kakao_login_url, get_kakao_access_token, get_kakao_user_info
from db.database import get_user_by_name, create_user, create_user_token

router = APIRouter()

# 1. 카카오 로그인 제공
@router.get("/auth/kakao/login-url", response_model=ResponseSchema)
def kakao_login_url():
    login_url = get_kakao_login_url()
    return ResponseSchema(
                status=200,
                msg="login_url 발급",
                data= {
                    "loginUrl" : login_url
                }
            )

@router.get("/auth/kakao/callback", response_model=ResponseSchema)
def kakao_callback(code: str):
    """
    안드로이드 앱이 인가 코드를 서버로 전달하면,
    서버가 이를 사용해 카카오에서 액세스 토큰을 가져옵니다.
    """
    try:
        # 1. Access Token 발급
        token_data = get_kakao_access_token(code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        if not access_token or not refresh_token:
            return ResponseSchema(
                status=400,
                msg="토큰 발급 실패",
                data=None
            )

        # 2. 사용자 정보 가져오기
        nickname = get_kakao_user_info(access_token)
        if not nickname:
            return ResponseSchema(
                status=401,
                msg="닉네임 정보를 가져올 수 없습니다.",
                data=None
            )

        # 3. DB에서 회원 여부 확인
        user = get_user_by_name(nickname)
        if not user:
            # 3-1. 회원이 아니면 신규 사용자 생성
            uuid = create_user(nickname)

            # 3-2. 토큰 정보 저장
            user_token = create_user_token(uuid)

            return ResponseSchema(
                status=201,
                msg="회원가입 완료",
                data={
                    "nickname": nickname,
                    "accessToken": user_token,
                }
            )

        # 4. 기존 회원이면 토큰 업데이트
        user_token = create_user_token(user['id'])

        return ResponseSchema(
            status=200,
            msg="로그인 성공",
            data={
                "nickname": nickname,
                "accessToken": user_token,
            }
        )

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="카카오 인증 중 서버 내부 오류",
            data={"error": str(e)}
        )