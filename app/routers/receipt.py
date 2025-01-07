from fastapi import APIRouter, HTTPException
from schemas.response import ResponseSchema
from db.database import get_receipt_items_by_room_id, update_user_item_check, count_checked_users_by_receipt_item_id
from schemas.receipt import UpdateCheckRequest

router = APIRouter()
@router.post("/updateChecks", response_model=ResponseSchema)
async def update_checks(request: UpdateCheckRequest):
    """
    클라이언트로부터 userUuid와 여러 receiptItemId, checked 상태를 받아 데이터베이스 업데이트
    """
    try:
        check_counts = {}

        # 각 receiptItemId와 checked 상태 업데이트
        for update in request.updates:
            is_updated = update_user_item_check(
                receipt_item_id=update.receiptItemId,
                user_uuid=request.userUuid,
                checked=update.checked
            )

            if not is_updated:
                raise HTTPException(status_code=400, detail=f"데이터 업데이트 실패: receiptItemId={update.receiptItemId}")

            # 업데이트 후 해당 receiptItemId의 체크된 사용자 수 계산
            count = count_checked_users_by_receipt_item_id(update.receiptItemId)
            check_counts[update.receiptItemId] = count

        return ResponseSchema(
            status=200,
            msg="데이터 업데이트 성공",
            data={"checkCounts": check_counts}
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="서버 내부 오류",
            data={"error": str(e)}
        )



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