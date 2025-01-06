import base64
import json
import os
from openai import OpenAI

# OpenAI API 키 환경 변수
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

async def analyze_receipt_logic(file):
    """
    업로드된 영수증 이미지를 OpenAI API로 분석합니다.
    """
    # 파일 읽기
    file_content = await file.read()

    # 파일 타입 (예: image/jpeg)
    img_type = file.content_type

    # Base64로 인코딩
    img_b64_str = base64.b64encode(file_content).decode("utf-8")

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=OPENAI_KEY)

    # 분석 요청 프롬프트
    prompt = """
    너는 영수증 데이터를 분석해서 결과를 JSON 형식으로 반환하는 전문가야. 아래 영수증 텍스트에서 메뉴 이름, 세부사항, 가격을 탐지하고 총합을 계산하거나 제공된 총합을 검증해. 결과는 아래 JSON 형식에 따라 작성해줘.

    입력: [영수증 텍스트 입력]

    JSON 출력 형식:

    {
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

    # OpenAI API 호출
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

    # 응답에서 필요한 데이터 추출
    response_dict = response.to_dict()
    row_data = response_dict["choices"][0]["message"]["content"]

    # JSON 파싱
    start = row_data.find("{")
    end = row_data.rfind("}") + 1
    json_string = row_data[start:end]
    data = json.loads(json_string)

    return data