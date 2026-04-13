from fastapi import APIRouter

router = APIRouter(prefix="/passengers", tags=["passengers"])


@router.get("/me")
async def get_profile() -> dict[str, str]:
    return {"message": "Passenger profile placeholder"}
