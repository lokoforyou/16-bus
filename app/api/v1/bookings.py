from fastapi import APIRouter, Depends, status

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.bookings.schemas import (
    BookingCancelResponse,
    BookingCreatedResponse,
    BookingDetailResponse,
    BookingListResponse,
    BookingPaymentResponse,
    BookingQuoteRequest,
    BookingQuoteResponse,
    CreateBookingAdminRequest,
    CreateBookingRequest,
)
from app.domain.payments.schemas import PaymentRequest

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/quote", response_model=BookingQuoteResponse)
async def quote_booking(
    request: BookingQuoteRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingQuoteResponse:
    return services.bookings.quote(request)


@router.post("", response_model=BookingCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: CreateBookingRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingCreatedResponse:
    return services.bookings.create(request)


@router.post("/admin", response_model=BookingCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_booking_admin(
    request: CreateBookingAdminRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingCreatedResponse:
    return services.bookings.create_admin(request)


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingDetailResponse:
    return services.bookings.get(booking_id)


@router.post("/{booking_id}/pay", response_model=BookingPaymentResponse)
async def pay_booking(
    booking_id: str,
    request: PaymentRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingPaymentResponse:
    return services.bookings.pay(booking_id, request)


@router.post("/{booking_id}/cancel", response_model=BookingCancelResponse)
async def cancel_booking(
    booking_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingCancelResponse:
    return services.bookings.cancel(booking_id)


@router.get("/admin", response_model=BookingListResponse)
async def list_bookings_admin(
    services: ApplicationServices = Depends(get_application_services),
) -> BookingListResponse:
    return BookingListResponse(items=services.bookings.list_all())


@router.get("/admin/{booking_id}", response_model=BookingDetailResponse)
async def get_booking_admin(
    booking_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingDetailResponse:
    return services.bookings.get_admin(booking_id)


@router.post("/admin/{booking_id}/cancel", response_model=BookingCancelResponse)
async def cancel_booking_admin(
    booking_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> BookingCancelResponse:
    return services.bookings.cancel_admin(booking_id)
