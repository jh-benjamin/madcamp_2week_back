from fastapi import FastAPI, UploadFile, File, HTTPException
from schemas.response import ResponseSchema
from services.receipt_service import analyze_receipt_logic
from routers.auth import router as auth_router  # auth 라우터 가져오기
from routers.rooms import router as room_router  # room 라우터
from db.database import get_user_by_name

app = FastAPI()

# 라우터 등록
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(room_router, prefix="/rooms", tags=["Rooms"])
    
@app.post("/analyzeReceiptByGpt", response_model=ResponseSchema)
async def analyze_receipt(file: UploadFile = File(...)):
    """
    업로드된 영수증 이미지를 OpenAI API로 분석하고,
    분석한 내용을 Json으로 반환합니다.
    """
    try:
        data = await analyze_receipt_logic(file)

        return ResponseSchema(
            status=200,
            msg="영수증 분석 성공",
            data=data
        )

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="영수증 분석 중 서버 내부 오류",
            data={"error": str(e)}
        )
    