from datetime import UTC, datetime
from uuid import uuid4
from app.domain.payments.models import PaymentORM
from app.domain.payments.provider_contracts import PaymentProvider
from app.domain.payments.repository import PaymentRepository

class PaymentService:
    def __init__(self, repository: PaymentRepository, provider: PaymentProvider):
        self.repository = repository
        self.provider = provider

    def process_payment(self, amount: float, method: str, booking_id: str) -> PaymentORM:
        txn_id = self.provider.initialize(amount, booking_id)
        success = self.provider.capture(txn_id)
        
        if not success:
            raise Exception("Payment failed")
            
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
