from app.domain.routes.repository import RouteRepository
from app.domain.routes.schemas import RouteListResponse, RouteStopListResponse


class RouteService:
    def __init__(self, repository: RouteRepository) -> None:
        self.repository = repository

    def list_routes(self) -> RouteListResponse:
        return RouteListResponse(items=self.repository.list_routes())

    def list_route_stops(self, route_id: str) -> RouteStopListResponse:
        return RouteStopListResponse(
            route_id=route_id,
            items=self.repository.list_route_stops(route_id),
        )
