from fastapi import WebSocket

active_connections = []

async def connect(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

async def broadcast(message: str):
    for connection in active_connections:
        await connection.send_text(message)

def disconnect(websocket: WebSocket):
    if websocket in active_connections:
        active_connections.remove(websocket)
