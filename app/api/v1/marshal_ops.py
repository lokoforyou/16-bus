from fastapi import APIRouter

router = APIRouter(prefix="/rank", tags=["rank-ops"])


@router.post("/tickets")
async def create_ticket() -> dict[str, str]:
    return {"message": "Rank ticket placeholder"}


@router.post("/cash-bookings/authorize")
async def authorize_cash_booking() -> dict[str, str]:
    return {"message": "Cash authorization placeholder"}


@router.post("/trips/{trip_id}/open")
async def open_trip_boarding(trip_id: str) -> dict[str, str]:
    return {"trip_id": trip_id, "state": "boarding"}


@router.post("/trips/{trip_id}/depart")
async def depart_trip(trip_id: str) -> dict[str, str]:
    return {"trip_id": trip_id, "state": "enroute"}


@router.get("/reconciliation/current")
async def get_current_reconciliation() -> dict[str, str]:
    return {"message": "Rank reconciliation placeholder"}
