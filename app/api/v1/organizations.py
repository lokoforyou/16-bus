from fastapi import APIRouter

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/{organization_id}/routes")
async def create_route(organization_id: str) -> dict[str, str]:
    return {"organization_id": organization_id, "message": "Route creation placeholder"}
