from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_payment_service
from app.domain.payments.schemas import PaymentDetailResponse
from app.domain.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentDetailResponse:
    payment = payment_service.get_payment(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
