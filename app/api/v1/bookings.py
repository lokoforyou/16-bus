from fastapi import APIRouter, Depends, status

from app.api.deps import get_booking_service, get_current_user_token
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_role
from app.domain.auth.schemas import TokenData
from app.domain.bookings.schemas import (
    BookingCancelResponse,
    BookingCreatedResponse,
    BookingDetailResponse,
    BookingPaymentResponse,
    BookingQuoteRequest,
    BookingQuoteResponse,
    CreateBookingRequest,
)
from app.domain.bookings.service import BookingService
from app.domain.payments.schemas import PaymentRequest

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/quote", response_model=BookingQuoteResponse)
async def quote_booking(
    request: BookingQuoteRequest,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingQuoteResponse:
    return booking_service.quote(request)


@router.post(
    "",
    response_model=BookingCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    request: CreateBookingRequest,
    booking_service: BookingService = Depends(get_booking_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> BookingCreatedResponse:
    check_role(token_data, [UserRole.PASSENGER])
    return booking_service.create_booking(request, passenger_id=token_data.user_id)


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> BookingDetailResponse:
    check_role(token_data, [UserRole.PASSENGER])
    return booking_service.get_booking(booking_id, passenger_id=token_data.user_id)


@router.post("/{booking_id}/pay", response_model=BookingPaymentResponse)
async def pay_booking(
    booking_id: str,
    request: PaymentRequest,
    booking_service: BookingService = Depends(get_booking_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> BookingPaymentResponse:
    check_role(token_data, [UserRole.PASSENGER])
    return booking_service.pay_booking(booking_id, request, passenger_id=token_data.user_id)


@router.post("/{booking_id}/cancel", response_model=BookingCancelResponse)
async def cancel_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> BookingCancelResponse:
    check_role(token_data, [UserRole.PASSENGER])
    return booking_service.cancel_booking(booking_id, passenger_id=token_data.user_id)


@router.post("/maintenance/expire-holds")
async def expire_holds(
    booking_service: BookingService = Depends(get_booking_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> dict[str, int]:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    expired = booking_service.expire_stale_holds()
    return {"expired": expired}
