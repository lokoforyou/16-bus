class MapsProvider:
    """Adapter boundary for routing, distance, and ETA lookups."""

    async def estimate_eta(self) -> dict[str, str]:
        return {"status": "not_implemented"}
