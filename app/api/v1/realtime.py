from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/trips/{trip_id}")
async def trip_updates(websocket: WebSocket, trip_id: str) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "trip_id": trip_id})
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "trip_id": trip_id})
            else:
                await websocket.send_json({"type": "ack", "trip_id": trip_id, "echo": message})
    except WebSocketDisconnect:
        return
