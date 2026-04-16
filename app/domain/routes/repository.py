from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM


class RouteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_route(self, route_id: str) -> RouteORM | None:
        return self.session.get(RouteORM, route_id)

    def list_routes(self) -> list[RouteORM]:
        return list(self.session.scalars(select(RouteORM)).all())

    def list_stops(self, active_only: bool = False) -> list[StopORM]:
        stmt = select(StopORM).order_by(StopORM.name.asc())
        if active_only:
            stmt = stmt.where(StopORM.active.is_(True))
        return list(self.session.scalars(stmt).all())

    def get_variant(self, variant_id: str) -> RouteVariantORM | None:
        return self.session.get(RouteVariantORM, variant_id)

    def get_stop(self, stop_id: str) -> StopORM | None:
        return self.session.get(StopORM, stop_id)

    def list_route_stops(self, route_id: str) -> list[RouteStopORM]:
        stmt = (
            select(RouteStopORM)
            .join(RouteVariantORM, RouteVariantORM.id == RouteStopORM.route_variant_id)
            .where(RouteVariantORM.route_id == route_id)
            .order_by(RouteStopORM.sequence_number.asc())
        )
        return list(self.session.scalars(stmt).all())

    def get_stop_sequence(self, route_variant_id: str, stop_id: str) -> int | None:
        stmt = select(RouteStopORM.sequence_number).where(
            RouteStopORM.route_variant_id == route_variant_id,
            RouteStopORM.stop_id == stop_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_sequence(self, route_variant_id: str, sequence_number: int) -> RouteStopORM | None:
        stmt = select(RouteStopORM).where(
            RouteStopORM.route_variant_id == route_variant_id,
            RouteStopORM.sequence_number == sequence_number,
        )
        return self.session.scalars(stmt).first()

    def validate_stop_order(
        self,
        route_variant_id: str,
        origin_stop_id: str,
        destination_stop_id: str,
    ) -> bool:
        origin_sequence = self.get_stop_sequence(route_variant_id, origin_stop_id)
        destination_sequence = self.get_stop_sequence(route_variant_id, destination_stop_id)
        return (
            origin_sequence is not None
            and destination_sequence is not None
            and origin_sequence < destination_sequence
        )

    def create_route(self, route: RouteORM) -> RouteORM:
        self.session.add(route)
        self.session.flush()
        self.session.refresh(route)
        return route

    def create_variant(self, variant: RouteVariantORM) -> RouteVariantORM:
        self.session.add(variant)
        self.session.flush()
        self.session.refresh(variant)
        return variant

    def create_route_stop(self, route_stop: RouteStopORM) -> RouteStopORM:
        self.session.add(route_stop)
        self.session.flush()
        self.session.refresh(route_stop)
        return route_stop

    def create_stop(self, stop: StopORM) -> StopORM:
        self.session.add(stop)
        self.session.flush()
        self.session.refresh(stop)
        return stop

    def update_stop(self, stop: StopORM) -> StopORM:
        self.session.add(stop)
        self.session.flush()
        self.session.refresh(stop)
        return stop

    def delete_stop(self, stop: StopORM) -> None:
        self.session.delete(stop)
        self.session.flush()
