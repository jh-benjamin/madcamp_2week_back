from fastapi import APIRouter, HTTPException
from schemas.response import ResponseSchema
from auth.kakao import get_kakao_login_url, get_kakao_access_token, get_kakao_user_info
from db.database import get_user_by_name, create_user, create_user_token
from schemas.auth import UserRequest, UserResponse
from auth.google import get_google_user_info

router = APIRouter()

# 1. 카카오 로그인 제공
@router.get("/kakao/login-url", response_model=ResponseSchema)
def kakao_login_url():
    """
    카카오 로그인 링크를 넘겨줍니다. (테스트용)
    """
    login_url = get_kakao_login_url()
    return ResponseSchema(
                status=200,
                msg="login_url 발급",
                data= {
                    "loginUrl" : login_url
                }
            )

@router.get("/kakao/callback", response_model=ResponseSchema)
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

# FastAPI 엔드포인트
@router.post("/google", response_model=ResponseSchema)
def google_login(request: UserRequest):
    """
    구글 로그인을 진행합니다.
    토큰 오류거나 api 오류일 가능성이 있습니다. (미완)
    """
    token = request.token

    try:
        # Step 1: Google People API로 사용자 정보 확인
        google_user_info = get_google_user_info(token)

        if not google_user_info:
            raise HTTPException(status_code=400, detail="Google 사용자 정보를 가져올 수 없습니다.")

        name = google_user_info.get("name")

        if not name:
            raise HTTPException(status_code=400, detail="Google 사용자 정보에 name이 없습니다.")

        # Step 2: 데이터베이스에서 사용자 확인
        uuid = get_user_by_name(name)

        if not user:
            # Step 3: 사용자가 존재하지 않을 경우 새 사용자 생성
            user = create_user(name=name)
            if not user:
                raise HTTPException(status_code=500, detail="사용자 생성 중 오류가 발생했습니다.")

        # Step 4: 사용자 토큰 생성
        token = create_user_token(user_id=uuid)
        if not token:
            raise HTTPException(status_code=500, detail="사용자 토큰 생성 중 오류가 발생했습니다.")

        return ResponseSchema(
            status=200,
            msg="Google 로그인 성공",
            data={
                "user": {
                    "id": uuid,
                    "name": name,
                },
                "token": token
            }
        )
    except HTTPException as http_err:
        # FastAPI에서 발생한 HTTP 오류 처리
        return ResponseSchema(
            status=500,
            msg="Google 로그인 중 FastAPI 오류 발생",
            data={str(http_err)}
        )
    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="Google 로그인 중 오류 발생",
            data={str(e)}
        )