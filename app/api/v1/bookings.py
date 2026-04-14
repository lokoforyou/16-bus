from fastapi import APIRouter, Depends, status

from app.api.deps import get_booking_service
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



# This endpoint is public and returns a ranked list of eligible trip candidates.
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
    token_data: TokenData = Depends(get_current_user_token),
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingCreatedResponse:
    return booking_service.create_booking(token_data.user_id, request.route_id, request.origin_stop_id, request.destination_stop_id, request.party_size, request.booking_channel)


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    return booking_service.get_booking(booking_id)


@router.post("/{booking_id}/pay", response_model=BookingPaymentResponse)
async def pay_booking(
    booking_id: str,
    request: PaymentRequest,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingPaymentResponse:
    return booking_service.pay_booking(booking_id, request)


@router.post("/{booking_id}/cancel", response_model=BookingCancelResponse)
async def cancel_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingCancelResponse:
    return booking_service.cancel_booking(booking_id)
