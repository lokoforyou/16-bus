from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.qr.schemas import BoardingScanRequest, BoardingScanResponse

router = APIRouter(prefix="/qr", tags=["qr"])


@router.post("/scan", response_model=BoardingScanResponse)
async def scan_qr(
    request: BoardingScanRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> BoardingScanResponse:
    return services.qr.scan(request)
