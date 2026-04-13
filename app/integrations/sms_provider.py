class SmsProvider:
    """Adapter boundary for SMS notifications."""

    async def send(self, phone_number: str, message: str) -> dict[str, str]:
        return {"phone_number": phone_number, "status": "queued", "message": message}
