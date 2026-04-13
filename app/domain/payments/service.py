from app.domain.payments.repository import PaymentRepository
from app.domain.payments.schemas import PaymentDetailResponse


class PaymentService:
    def __init__(self, repository: PaymentRepository) -> None:
        self.repository = repository

    def get_payment(self, payment_id: str) -> PaymentDetailResponse | None:
        payment = self.repository.get(payment_id)
        if payment is None:
            return None
        return PaymentDetailResponse(payment=payment)
