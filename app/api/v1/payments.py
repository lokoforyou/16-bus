from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.payments.schemas import PaymentDetailResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(
    payment_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> PaymentDetailResponse:
    return services.payments.get(payment_id)
