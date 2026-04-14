from fastapi import APIRouter, WebSocket, Depends
from app.api.deps import get_current_user_token, get_trip_service
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_role, check_org_ownership
from app.domain.auth.schemas import TokenData
from app.domain.trips.service import TripService
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.events import subscribe, DomainEvent, emit_event # Import subscribe and emit_event

router = APIRouter(prefix="/realtime", tags=["realtime"])

# In-memory storage for active websocket subscriptions per trip
# Key: trip_id, Value: list of active websockets for that trip
active_trip_subscriptions: Dict[str, List[WebSocket]] = defaultdict(list)

async def handle_trip_event(event: DomainEvent):
    """Listener for trip events. Broadcasts events to subscribed websockets."""
    trip_id = event.payload.get("trip_id")
    if not trip_id:
        return # Ignore events without a trip_id

    # Find websockets subscribed to this trip_id
    if trip_id in _subscribers:
        for websocket in list(_subscribers[trip_id]): # Iterate over a copy
            try:
                await websocket.send_json(event.payload)
            except Exception as e:
                print(f"Error sending event to websocket for trip {trip_id}: {e}")
                # Optionally remove disconnected websockets here
                _subscribers[trip_id].remove(websocket)
                if not _subscribers[trip_id]:
                    del _subscribers[trip_id]

# Subscribe the handler to relevant events
subscribe("trip_created", handle_trip_event)
subscribe("trip_state_changed", handle_trip_event)

@router.websocket("/trips/{trip_id}")
async def trip_updates(
    websocket: WebSocket,
    trip_id: str,
    token_data: TokenData = Depends(get_current_user_token),
    trip_service: TripService = Depends(get_trip_service),
) -> None:
    trip = trip_service.get_trip(trip_id)

    if not trip:
        await websocket.close(code=1008, reason="Trip not found")
        return

    try:
        # Authorize based on role and organization ownership
        if token_data.role == UserRole.SUPER_ADMIN:
            pass  # Super admins can access any trip
        elif token_data.role in [UserRole.ORG_ADMIN, UserRole.DRIVER]:
            check_org_ownership(token_data, trip.organization_id)
        else:
            # For now, assume other roles (like Passenger) might have access via bookings,
            # but strict scope enforcement is needed. For simplicity, we'll grant access
            # if the org matches, or if it's SUPER_ADMIN.
            # A more complex check might involve fetching bookings for the user.
            # For now, we rely on org ownership for non-SUPER_ADMIN roles.
            raise PermissionDeniedError("Unauthorized access to trip updates")

    except (NotFoundError, PermissionDeniedError) as e:
        await websocket.close(code=1008, reason=str(e))
        return

    await websocket.accept()

    # Subscribe this websocket to events for the specific trip_id
    subscription_key = trip_id
    _subscribers[subscription_key].append(websocket)

    await websocket.send_json({"message": f"Connected to trip {trip_id} updates."})

    try:
        # Keep the connection open and wait for events to be pushed
        # In a more robust system, this loop might handle client messages or pings
        while True:
            # This loop keeps the connection alive. Events are pushed via handle_trip_event.
            # A more sophisticated approach would use asyncio.Queue to push events.
            # For now, we rely on the event loop handling the callbacks.
            await asyncio.sleep(1) 
    except asyncio.CancelledError:
        # Connection closed by client or server
        pass
    finally:
        # Clean up subscription upon disconnection
        if subscription_key in _subscribers and websocket in _subscribers[subscription_key]:
            _subscribers[subscription_key].remove(websocket)
            if not _subscribers[subscription_key]:
                del _subscribers[subscription_key]
        await websocket.close()


