from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_qr_service
from app.domain.qr.schemas import BoardingScanRequest, BoardingScanResponse
from app.domain.qr.service import QRService

router = APIRouter(prefix="/driver", tags=["driver-ops"])


@router.post("/shifts/start")
async def start_shift() -> dict[str, str]:
    return {"message": "Driver shift start placeholder"}


@router.post("/shifts/end")
async def end_shift() -> dict[str, str]:
    return {"message": "Driver shift end placeholder"}


@router.get("/trips/current")
async def get_current_trip() -> dict[str, str]:
    return {"message": "Current trip placeholder"}


@router.post("/boardings/scan", response_model=BoardingScanResponse)
async def scan_boarding(
    request: BoardingScanRequest,
    qr_service: QRService = Depends(get_qr_service),
) -> BoardingScanResponse:
    try:
        return qr_service.validate_and_scan(request)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail in {"QR token not found", "Booking not found"} else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/location")
async def post_location() -> dict[str, str]:
    return {"message": "Driver location update placeholder"}


@router.post("/incidents")
async def create_incident() -> dict[str, str]:
    return {"message": "Driver incident placeholder"}
