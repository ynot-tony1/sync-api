from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.connection_manager import connect, disconnect

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await connect(websocket)
    except Exception:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        disconnect(websocket)