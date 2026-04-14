from typing import List, Optional
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM
from app.domain.routes.repository import RouteRepository
from app.domain.routes.schemas import RouteCreate, RouteVariantCreate, RouteStopCreate


class RouteAdminService:
    def __init__(self, repository: RouteRepository):
        self.repository = repository

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
        route = self.repository.get_route(route_id)
        if not route:
            raise NotFoundError("Route not found")
        
        variant = RouteVariantORM(
            id=data.id,
            route_id=route_id,
            name=data.name,
            active=True,
        )
        return self.repository.create_variant(variant)

    def add_stop_to_variant(self, route_id: str, variant_id: str, data: RouteStopCreate) -> RouteStopORM:
        variant = self.repository.get_variant(variant_id)
        if not variant or variant.route_id != route_id:
            raise NotFoundError("Route variant not found")
        
        stop = self.repository.get_stop(data.stop_id)
        if not stop:
            raise NotFoundError("Stop not found")
            
        # Add validation for sequence ordering
        existing_sequence = self.repository.get_stop_sequence(variant_id, data.stop_id)
        if existing_sequence:
             raise ConflictError("Stop already exists in variant")

        route_stop = RouteStopORM(
            id=f"rs-{variant_id}-{data.stop_id}",
            route_variant_id=variant_id,
            stop_id=data.stop_id,
            sequence_number=data.sequence_number,
            dwell_time_seconds=data.dwell_time_seconds,
        )
        return self.repository.create_route_stop(route_stop)
