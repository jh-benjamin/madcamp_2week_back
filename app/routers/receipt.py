from fastapi import APIRouter, HTTPException
from schemas.response import ResponseSchema
from db.database import update_user_item_check, count_checked_users_by_receipt_item_id, get_receipt_items_by_room_id, get_receipt_id_by_room_id
from db.receipt import get_users_in_receipt, get_receipt_items_by_receipt_id, calculate_user_totals, calculate_user_checks_and_item_counts, update_is_paid, get_receipt_items_by_room_id, get_user_item_check_status
from schemas.receipt import UpdateCheckRequest

router = APIRouter()
@router.get("/getReceiptItemsWithCheckStatus/{room_id}/{user_uuid}", response_model=ResponseSchema)
async def get_receipt_items_with_check_status(room_id: int, user_uuid: str):
    """
    특정 roomId와 userUuid를 기반으로 메뉴명, 가격, 체크 여부를 반환하는 API
    """
    try:
        # Step 1: 해당 roomId의 receiptItems 가져오기
        receipt_items = get_receipt_items_by_room_id(room_id)
        if not receipt_items:
            return ResponseSchema(
                status=404,
                msg="해당 roomId에 대한 receiptItems가 없습니다.",
                data=None
            )

        # Step 2: 각 receiptItem에 대해 userUuid가 체크했는지 확인
        result = []
        for item in receipt_items:
            is_checked = get_user_item_check_status(receipt_item_id=item["id"], user_uuid=user_uuid)
            result.append({
                "itemName": item["itemName"],
                "price": item["price"],
                "checked": is_checked
            })

        return ResponseSchema(
            status=200,
            msg="메뉴와 체크 상태 조회 성공",
            data=result
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="서버 내부 오류",
            data={"error": str(e)}
        )
    

@router.post("/updateIsPaid", response_model=ResponseSchema)
async def update_is_paid_endpoint(room_id: int, user_uuid: str, is_paid: int):
    """
    roomId와 userUuid를 기반으로 isPaid 값을 업데이트하는 API
    """
    result = update_is_paid(room_id, user_uuid, is_paid)
    print(f"result:{result}")
    if result["status"] == "success":
        return ResponseSchema(
            status=200,
            msg=result["msg"],
            data=None
        )
    else:
        return ResponseSchema(
            status=500,
            msg=result["msg"],
            data={"error": result["error"]}
        )

@router.get("/getReceiptSummary/{room_id}", response_model=ResponseSchema)
async def get_receipt_summary(room_id: int):
    """
    receiptId를 기반으로 사용자별 메뉴 체크 상태와 금액 계산 결과 반환
    """
    try:
        # Step 0: room_id를 사용하여 receipt_id 조회
        receipt_id = get_receipt_id_by_room_id(room_id)
        if not receipt_id:
            return ResponseSchema(
                status=404,
                msg="해당 roomId에 대한 receiptId가 없습니다.",
                data=None
            )
        
        # Step 1: Receipt에 참여한 사용자 정보 가져오기
        participants = get_users_in_receipt(room_id)
        if not participants:
            return ResponseSchema(
                    status=404,
                    msg="해당 receiptId에 참여한 사용자가 없습니다.",
                    data=None
                )

        # Step 2: ReceiptItems 데이터 가져오기
        receipt_items = get_receipt_items_by_receipt_id(receipt_id)
        if not receipt_items:
            return ResponseSchema(
                    status=404,
                    msg="해당 receiptId에 대한 receiptItems가 없습니다.",
                    data=None
                )

        # Step 3: 사용자별 체크 상태 및 메뉴별 체크 인원 계산
        user_checks, item_check_counts = calculate_user_checks_and_item_counts(receipt_id)

        # Step 4: 사용자별 총 금액 계산
        user_totals = calculate_user_totals(user_checks, item_check_counts, receipt_items, room_id)

        # Step 5: 아무도 체크하지 않은 메뉴 확인
        unchecked_items = [
            item for item_id, item in receipt_items.items()
            if item_check_counts.get(item_id, 0) == 0
        ]

        # 데이터 반환
        result = {
            "participants": participants,
            "userChecks": user_checks,
            "userTotals": user_totals,
            "uncheckedItems": unchecked_items
        }

        return ResponseSchema(
            status=200,
            msg="영수증 요약 정보 조회 성공",
            data=result
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="서버 내부 오류",
            data={"error": str(e)}
        )

@router.get("/getReceiptId/{room_id}", response_model=ResponseSchema)
async def get_receipt_id(room_id: int):
    """
    roomId를 기반으로 receiptId를 반환
    """
    try:
        # 데이터베이스에서 receiptId 조회
        receipt_id = get_receipt_id_by_room_id(room_id)

        if not receipt_id:
            return ResponseSchema(
                status=404,
                msg="해당 roomId에 대한 receiptId가 없습니다",
                data=None
            )

        return ResponseSchema(
            status=200,
            msg="receiptId 조회 성공",
            data={"receiptId": receipt_id}
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        return ResponseSchema(
            status=500,
            msg="서버 내부 오류",
            data={"error": str(e)}
        )

@router.post("/updateChecks", response_model=ResponseSchema)
async def update_checks(request: UpdateCheckRequest):
    """
    클라이언트로부터 userUuid와 여러 receiptItemId, checked 상태를 받아 데이터베이스 업데이트
    """
    try:
        check_counts = {}

        # 각 receiptItemId와 checked 상태 업데이트
        print(f"request:{request}")
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


        print(f"check_counts: {check_counts}")

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



@router.get("/getReceiptItems/{room_id}", response_model=ResponseSchema)
async def get_receipt_items(room_id: int):
    """
    주어진 방 ID를 기반으로 receiptItems 데이터를 반환
    """
    try:
        # 데이터베이스에서 receiptItems 조회
        receipt_items = get_receipt_items_by_room_id(room_id)

        if not receipt_items:
            return ResponseSchema(
                status=404,
                msg="해당 방에 대한 receiptItems가 없습니다.",
                data=None
            )

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