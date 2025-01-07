from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from schemas.response import ResponseSchema

# Router 생성
router = APIRouter()

# WebSocket 연결을 관리할 dictionary
connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    """
    클라이언트가 WebSocket을 통해 서버와 연결
    """
    await websocket.accept()
    connections[uuid] = websocket  # uuid와 WebSocket 연결 매핑
    try:
        while True:
            data = await websocket.receive_text()  # 클라이언트 메시지 대기 (필요한 경우)
    except WebSocketDisconnect:
        del connections[uuid]  # 연결 끊어지면 제거

@router.post("/sendNotification", response_model=ResponseSchema)
async def send_notification(uuid: str, message: str):
    """
    특정 uuid에 해당하는 디바이스로 알림 전송
    """
    if uuid in connections:
        await connections[uuid].send_text(message)
        return ResponseSchema(
            status=200,
            msg=f"알림이 {uuid}에게 전송되었습니다.",
            data={"uuid": uuid, "message": message}
        )
    return ResponseSchema(
        status=404,
        msg="해당 uuid와 연결된 WebSocket이 없습니다.",
        data={"uuid": uuid}
    )