from auth.kakao import get_kakao_login_url, get_kakao_access_token, get_kakao_user_info
from fastapi import FastAPI, UploadFile, File
from schemas.response import ResponseSchema
from db.database import get_user_by_name, create_user, create_user_token
from openai import OpenAI
import base64
import os
from PIL import Image
import pytesseract
import io  # io 모듈 추가
import cv2
import numpy as np

app = FastAPI()

# 환경 변수에서 API 키 가져오기
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# 1. 카카오 로그인 제공
@app.get("/auth/kakao/login-url", response_model=ResponseSchema)
def kakao_login_url():
    login_url = get_kakao_login_url()
    return ResponseSchema(
                status=200,
                msg="login_url 발급",
                data= {
                    "loginUrl" : login_url
                }
            )

@app.get("/auth/kakao/callback", response_model=ResponseSchema)
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
    
@app.post("/analyze-receipt_gpt", response_model=ResponseSchema)
async def analyze_receipt(file: UploadFile = File(...)):
    """
    업로드된 영수증 이미지를 OpenAI API로 분석합니다.
    """
    try:

         # 파일 읽기
        file_content = await file.read()
        
        # 파일 타입 (예: image/jpeg)
        img_type = file.content_type
        
        # Base64로 인코딩
        img_b64_str = base64.b64encode(file_content).decode("utf-8")

        client = OpenAI(
            api_key=OPENAI_KEY
        )

        prompt = """
        너는 영수증 데이터를 분석해서 결과를 JSON 형식으로 반환하는 전문가야. 아래 영수증 텍스트에서 메뉴 이름, 세부사항, 가격을 탐지하고 총합을 계산하거나 제공된 총합을 검증해. 결과는 아래 JSON 형식에 따라 작성해줘.

        입력: [영수증 텍스트 입력]

        JSON 출력 형식:

        json{
        "items": [
            {
            "menu": "메뉴 이름",
            "details": "세부 사항",
            "price": 가격
            },
            ...
        ],
        "total_price": 총합
        }
        작업 시 유의사항:

        1. 메뉴 이름은 각 줄의 텍스트에서 추출해.
        2. 가격은 숫자로 표현하며, 뒤에 단위 ('원')을 추가해줘.
        3. 세부사항이 없으면 '없음'으로 기록해.
        4. 총합은 계산 결과 또는 제공된 값을 사용해. 제공된 값을 우선으로 갖고 와줘!
        5. 반환된 JSON 형식은 오류 없이 정확해야 해.
        6. 오로지 답변으로 JSON 형식만 출력해줘.
        7. OCR 쓰지 말고, 너가 직접 분석해봐. 코드로 분석하라는 이야기가 아니야.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{img_type};base64,{img_b64_str}"},
                        },
                    ],
                }
            ],
        )

        return ResponseSchema(
            status=200,
            msg="영수증 분석 성공",
            data=response
        )

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="영수증 분석 중 서버 내부 오류",
            data={"error": str(e)}
        )
    
@app.post("/analyze-receipt", response_model=dict)
async def analyze_receipt(file: UploadFile = File(...)):
    """
    업로드된 영수증 이미지를 분석하여 텍스트를 추출합니다.
    """
    try:
        # 업로드된 파일 읽기
        file_content = await file.read()
        
        # 전처리 후 OCR 실행
        image = preprocess_image(file_content)
        extracted_text = pytesseract.image_to_string(image, lang="kor+eng")
        
        # 텍스트 결과 반환
        return {
            "status": 200,
            "msg": "텍스트 추출 성공",
            "data": {
                "text": extracted_text
            }
        }
    
    except Exception as e:
        return {
            "status": 500,
            "msg": "텍스트 추출 중 오류 발생",
            "error": str(e)
        }
    
# 이미지 전처리
def preprocess_image(file_content):
    np_img = np.frombuffer(file_content, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    # 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 이진화
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # OpenCV 이미지 객체를 PIL 이미지 객체로 변환
    processed_image = Image.fromarray(binary)
    return processed_image