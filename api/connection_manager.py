from fastapi import WebSocket
from typing import List

active_connections: List[WebSocket] = []

async def connect(websocket: WebSocket) -> None:
    """
    Accepts a new WebSocket connection and adds it to the active connections list.
    
    Args:
        websocket (WebSocket): The incoming WebSocket connection.
    """
    await websocket.accept()
    active_connections.append(websocket)

async def broadcast(message: str) -> None:
    """
    Sends a text message to all active WebSocket connections.
    
    Args:
        message (str): The message to broadcast.
    """
    for connection in active_connections:
        await connection.send_text(message)

def disconnect(websocket: WebSocket) -> None:
    """
    Removes a WebSocket connection from the active connections list.
    
    Args:
        websocket (WebSocket): The WebSocket connection to remove.
    """
    if websocket in active_connections:
        active_connections.remove(websocket)
