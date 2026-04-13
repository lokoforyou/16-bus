class PaymentsProvider:
    """Adapter boundary for payment authorization and settlement."""

    async def authorize(self) -> dict[str, str]:
        return {"status": "not_implemented"}
