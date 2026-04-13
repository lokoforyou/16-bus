from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/trips/{trip_id}")
async def trip_updates(websocket: WebSocket, trip_id: str) -> None:
    await websocket.accept()
    await websocket.send_json({"trip_id": trip_id, "message": "Realtime placeholder"})
    await websocket.close()
