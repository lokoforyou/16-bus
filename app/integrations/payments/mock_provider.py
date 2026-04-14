import logging

logger = logging.getLogger("payments")

class MockPaymentProvider:
    def initialize(self, amount: float, reference: str) -> str:
        logger.info(f"Initializing payment of {amount} for {reference}")
        return f"txn_{reference}"
    
    def capture(self, transaction_id: str) -> bool:
        logger.info(f"Capturing payment {transaction_id}")
        return True
    
    def refund(self, transaction_id: str) -> bool:
        logger.info(f"Refunding payment {transaction_id}")
        return True
