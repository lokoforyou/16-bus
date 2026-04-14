from app.core.exceptions import ConflictError, NotFoundError
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM
from app.domain.routes.repository import RouteRepository
from app.domain.routes.schemas import RouteCreate, RouteStopCreate, RouteVariantCreate


class RouteAdminService:
    def __init__(self, repository: RouteRepository):
        self.repository = repository

    def get_route(self, route_id: str) -> RouteORM:
        route = self.repository.get_route(route_id)
        if route is None:
            raise NotFoundError("Route not found")
        return route

    def list_routes(self):
        return {"items": self.repository.list_routes()}

    def list_route_stops(self, route_id: str):
        self.get_route(route_id)
        return {"items": self.repository.list_route_stops(route_id)}

    def create_route(self, data: RouteCreate) -> RouteORM:
        route = RouteORM(
            id=data.id,
            organization_id=data.organization_id,
            code=data.code,
            name=data.name,
            direction=data.direction,
            active=True,
        )
        return self.repository.create_route(route)

    def create_variant(self, route_id: str, data: RouteVariantCreate) -> RouteVariantORM:
        self.get_route(route_id)
        variant = RouteVariantORM(id=data.id, route_id=route_id, name=data.name, active=True)
        return self.repository.create_variant(variant)

    def add_stop_to_variant(self, route_id: str, variant_id: str, data: RouteStopCreate) -> RouteStopORM:
        variant = self.repository.get_variant(variant_id)
        if not variant or variant.route_id != route_id:
            raise NotFoundError("Route variant not found")

        stop = self.repository.get_stop(data.stop_id)
        if not stop:
            raise NotFoundError("Stop not found")

        if self.repository.get_stop_sequence(variant_id, data.stop_id) is not None:
            raise ConflictError("Stop already exists in variant")
        if self.repository.get_by_sequence(variant_id, data.sequence_number) is not None:
            raise ConflictError("Sequence number already exists for variant")

        route_stop = RouteStopORM(
            id=f"rs-{variant_id}-{data.stop_id}",
            route_variant_id=variant_id,
            stop_id=data.stop_id,
            sequence_number=data.sequence_number,
            dwell_time_seconds=data.dwell_time_seconds,
        )
        return self.repository.create_route_stop(route_stop)
