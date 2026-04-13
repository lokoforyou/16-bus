from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login() -> dict[str, str]:
    return {"message": "Authentication flow placeholder"}
