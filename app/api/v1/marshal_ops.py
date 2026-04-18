from fastapi import APIRouter, Depends, status

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.ranks.schemas import (
    RankCashAuthorizationRequest,
    RankQueueTicketRead,
    RankTicketAssignRequest,
    RankTicketIssueRequest,
)
from app.domain.ranks.models import RankQueueTicketORM

router = APIRouter(prefix="/rank", tags=["rank-ops"])


@router.post("/tickets", response_model=RankQueueTicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: RankTicketIssueRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> RankQueueTicketRead:
    return services.ranks.issue_ticket(request)


@router.post("/tickets/assign", response_model=RankQueueTicketRead)
async def assign_ticket(
    request: RankTicketAssignRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> RankQueueTicketRead:
    return services.ranks.assign_ticket(request)


@router.post("/tickets/{ticket_id}/board", response_model=RankQueueTicketRead)
async def board_ticket(
    ticket_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> RankQueueTicketRead:
    return services.ranks.board_ticket(ticket_id)


@router.post("/cash-bookings/authorize")
async def authorize_cash_booking(
    request: RankCashAuthorizationRequest,
    services: ApplicationServices = Depends(get_application_services),
) -> dict[str, object]:
    return services.ranks.authorize_cash_booking(request)


@router.post("/trips/{trip_id}/open")
async def open_trip_boarding(
    trip_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> dict[str, str]:
    return services.ranks.open_trip(trip_id)


@router.post("/trips/{trip_id}/depart")
async def depart_trip(
    trip_id: str,
    services: ApplicationServices = Depends(get_application_services),
) -> dict[str, str]:
    return services.ranks.depart_trip(trip_id)


@router.get("/reconciliation/current")
async def get_current_reconciliation(
    services: ApplicationServices = Depends(get_application_services),
) -> dict[str, object]:
    tickets = services.session.query(RankQueueTicketORM).all()
    return {
        "status": "ok",
        "tickets_total": len(tickets),
        "tickets_boarded": sum(1 for ticket in tickets if ticket.state == "boarded"),
        "tickets_assigned": sum(1 for ticket in tickets if ticket.state == "assigned"),
    }
