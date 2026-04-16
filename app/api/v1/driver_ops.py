from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.shifts.schemas import Shift, ShiftCreate

router = APIRouter(prefix="/driver/shifts", tags=["driver-ops"])


@router.post("/start", response_model=Shift)
async def start_shift(
    data: ShiftCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.shifts.start(data)


@router.post("/{shift_id}/end", response_model=Shift)
async def end_shift(
    shift_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.shifts.end(shift_id)


@router.get("/current", response_model=Shift)
async def get_current_shift(
    services: ApplicationServices = Depends(get_application_services),
):
    return services.shifts.current()
