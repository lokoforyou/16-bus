from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM


class RouteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_routes(self) -> list[RouteORM]:
        statement: Select[tuple[RouteORM]] = select(RouteORM).order_by(RouteORM.name)
        return list(self.session.scalars(statement))

    def get_route(self, route_id: str) -> RouteORM | None:
        return self.session.get(RouteORM, route_id)

    def get_variant_for_route(self, route_id: str) -> RouteVariantORM | None:
        statement = (
            select(RouteVariantORM)
            .where(RouteVariantORM.route_id == route_id, RouteVariantORM.active.is_(True))
            .limit(1)
        )
        return self.session.scalars(statement).first()

    def list_route_stops(self, route_id: str) -> list[dict]:
        variant = self.get_variant_for_route(route_id)
        if variant is None:
            return []

        statement = (
            select(RouteStopORM, StopORM)
            .join(StopORM, StopORM.id == RouteStopORM.stop_id)
            .where(RouteStopORM.route_variant_id == variant.id)
            .order_by(RouteStopORM.sequence_number)
        )
        rows = self.session.execute(statement).all()
        return [
            {
                "id": stop.id,
                "name": stop.name,
                "type": stop.type,
                "lat": stop.lat,
                "lon": stop.lon,
                "cash_allowed": stop.cash_allowed,
                "sequence_number": route_stop.sequence_number,
                "dwell_time_seconds": route_stop.dwell_time_seconds,
            }
            for route_stop, stop in rows
        ]

    def get_stop(self, stop_id: str) -> StopORM | None:
        return self.session.get(StopORM, stop_id)

    def get_stop_sequence(self, route_variant_id: str, stop_id: str) -> int | None:
        statement = (
            select(RouteStopORM.sequence_number)
            .where(
                RouteStopORM.route_variant_id == route_variant_id,
                RouteStopORM.stop_id == stop_id,
            )
            .limit(1)
        )
        return self.session.scalar(statement)

    def validate_stop_order(
        self, route_variant_id: str, origin_stop_id: str, destination_stop_id: str
    ) -> bool:
        origin_sequence = self.get_stop_sequence(route_variant_id, origin_stop_id)
        destination_sequence = self.get_stop_sequence(route_variant_id, destination_stop_id)
        if origin_sequence is None or destination_sequence is None:
            return False
        return destination_sequence > origin_sequence
