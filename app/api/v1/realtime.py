import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.deps import decode_token_to_token_data
from app.application import actor_from_token_data, build_application_services
from app.core.database import get_session_factory
from app.core.events import DomainEvent, subscribe

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/trips/{trip_id}")
async def trip_updates(
    websocket: WebSocket,
    trip_id: str,
    token: str | None = Query(default=None),
) -> None:
    session = get_session_factory()()
    actor = actor_from_token_data(decode_token_to_token_data(token), source="websocket")
    services = build_application_services(session=session, actor=actor, request_source="websocket")
    queue: asyncio.Queue[DomainEvent] = asyncio.Queue()

    def listener(event: DomainEvent) -> None:
        if event.payload.get("trip_id") == trip_id:
            queue.put_nowait(event)

    unsubscribe_created = subscribe("trip.created", listener)
    unsubscribe_changed = subscribe("trip.state_changed", listener)
    try:
        services.trips.get(trip_id)
        await websocket.accept()
        await websocket.send_json({"type": "connected", "trip_id": trip_id})
        while True:
            event = await queue.get()
            await websocket.send_json({"type": "event", "trip_id": trip_id, "event": event.payload | {"name": event.name}})
    except WebSocketDisconnect:
        return
    finally:
        unsubscribe_created()
        unsubscribe_changed()
        session.close()
        try:
            await websocket.close()
        except RuntimeError:
            pass
