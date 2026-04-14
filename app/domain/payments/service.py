from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import DomainRuleViolationError
from app.domain.payments.models import PaymentORM
from app.domain.payments.provider_contracts import PaymentProvider
from app.domain.payments.repository import PaymentRepository
from app.domain.payments.schemas import PaymentDetailResponse, PaymentRead


class PaymentService:
    def __init__(self, repository: PaymentRepository, provider: PaymentProvider):
        self.repository = repository
        self.provider = provider

    def process_payment(self, amount: float, method: str, booking_id: str) -> PaymentORM:
        txn_id = self.provider.initialize(amount, booking_id)
        success = self.provider.capture(txn_id)
        if not success:
            raise DomainRuleViolationError("Payment failed")

        payment = PaymentORM(
            id=f"payment-{uuid4().hex[:12]}",
            booking_id=booking_id,
            method=method,
            amount=amount,
            status="captured",
            reference=txn_id,
            settled_at=datetime.now(UTC),
        )
        return self.repository.save(payment)

    def refund_payment(self, booking_id: str) -> PaymentORM | None:
        latest = self.repository.get_latest_for_booking(booking_id)
        if latest is None:
            return None
        latest.status = "refunded"
        return self.repository.save(latest)

    def get_payment(self, payment_id: str) -> PaymentDetailResponse | None:
        payment = self.repository.get_by_id(payment_id)
        if payment is None:
            return None
        return PaymentDetailResponse(payment=PaymentRead.model_validate(payment))
