from fastapi import APIRouter

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/status")
async def get_compliance_status() -> dict[str, str]:
    return {"message": "Compliance status placeholder"}
