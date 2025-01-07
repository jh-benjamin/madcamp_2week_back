from fastapi import APIRouter, HTTPException
from schemas.response import ResponseSchema
from db.database import get_receipt_items_by_room_id

router = APIRouter()

@router.get("/getReceiptItems", response_model=ResponseSchema)
async def get_receipt_items(room_id: int):
    """
    주어진 방 ID를 기반으로 receiptItems 데이터를 반환
    """
    try:
        # 데이터베이스에서 receiptItems 조회
        receipt_items = get_receipt_items_by_room_id(room_id)

        if not receipt_items:
            raise HTTPException(status_code=404, detail="해당 방에 대한 receiptItems가 없습니다.")

        return ResponseSchema(
            status=200,
            msg="receiptItems 조회 성공",
            data=receipt_items
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="서버 내부 오류",
            data={"error": str(e)}
        )