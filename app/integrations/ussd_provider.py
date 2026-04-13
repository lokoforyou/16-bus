class UssdProvider:
    """Adapter boundary for feature-phone USSD flows."""

    async def start_session(self, session_id: str) -> dict[str, str]:
        return {"session_id": session_id, "status": "not_implemented"}
