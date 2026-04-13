from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_booking_service
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
) -> BookingCreatedResponse:
    try:
        return booking_service.create_booking(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingDetailResponse:
    booking = booking_service.get_booking(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/{booking_id}/pay", response_model=BookingPaymentResponse)
async def pay_booking(
    booking_id: str,
    request: PaymentRequest,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingPaymentResponse:
    try:
        return booking_service.pay_booking(booking_id, request)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Booking not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/{booking_id}/cancel", response_model=BookingCancelResponse)
async def cancel_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingCancelResponse:
    try:
        return booking_service.cancel_booking(booking_id)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Booking not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
