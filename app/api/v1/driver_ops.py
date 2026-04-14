from fastapi import APIRouter, Depends
from app.api.deps import get_shift_service, get_current_user_token
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_role
from app.domain.auth.schemas import TokenData
from app.domain.shifts.models import DriverShiftORM
from app.domain.shifts.schemas import Shift, ShiftCreate
from app.domain.shifts.service import ShiftService

router = APIRouter(prefix="/driver/shifts", tags=["driver-ops"])


@router.post("/start", response_model=Shift)
async def start_shift(
    data: ShiftCreate,
    shift_service: ShiftService = Depends(get_shift_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> DriverShiftORM:
    check_role(token_data, [UserRole.DRIVER])
    return shift_service.start_shift(data, actor_user_id=token_data.user_id)


@router.post("/{shift_id}/end", response_model=Shift)
async def end_shift(
    shift_id: str,
    shift_service: ShiftService = Depends(get_shift_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> DriverShiftORM:
    check_role(token_data, [UserRole.DRIVER])
    return shift_service.end_shift(shift_id, actor_user_id=token_data.user_id)


@router.get("/current", response_model=Shift)
async def get_current_shift(
    shift_service: ShiftService = Depends(get_shift_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> DriverShiftORM:
    check_role(token_data, [UserRole.DRIVER])
    return shift_service.get_active_shift_for_driver(token_data.user_id)
