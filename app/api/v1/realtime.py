import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import event_channel

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/trips/{trip_id}")
async def trip_updates(websocket: WebSocket, trip_id: str) -> None:
    await websocket.accept()
    topic = f"trip:{trip_id}"
    queue: asyncio.Queue[dict] = asyncio.Queue()

    async def enqueue(payload: dict) -> None:
        await queue.put(payload)

    event_channel.subscribe(topic, enqueue)
    await websocket.send_json({"type": "connected", "trip_id": trip_id, "topic": topic})
    try:
        while True:
            receive_task = asyncio.create_task(websocket.receive_json())
            event_task = asyncio.create_task(queue.get())
            done, pending = await asyncio.wait({receive_task, event_task}, return_when=asyncio.FIRST_COMPLETED)

            if receive_task in done:
                message = receive_task.result()
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "trip_id": trip_id})
                else:
                    await websocket.send_json({"type": "ack", "trip_id": trip_id, "echo": message})
            if event_task in done:
                event_payload = event_task.result()
                await websocket.send_json({"type": "event", "trip_id": trip_id, "event": event_payload})

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    except WebSocketDisconnect:
        return
    finally:
        event_channel.unsubscribe(topic, enqueue)
