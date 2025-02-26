"""
WebSocket routes.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.connection_manager import connect, disconnect

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint that echoes received messages.
    
    Args:
        websocket (WebSocket): The incoming WebSocket connection.
    """
    try:
        await connect(websocket)
    except Exception:
        return
    try:
        while True:
            data: str = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        disconnect(websocket)
