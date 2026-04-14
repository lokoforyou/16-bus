from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.routes.models import RouteORM, RouteStopORM, RouteVariantORM, StopORM

class RouteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_route(self, route_id: str) -> RouteORM | None:
        return self.session.get(RouteORM, route_id)

    def get_variant(self, variant_id: str) -> RouteVariantORM | None:
        return self.session.get(RouteVariantORM, variant_id)

    def get_stop(self, stop_id: str) -> StopORM | None:
        return self.session.get(StopORM, stop_id)

    def get_stop_sequence(self, route_variant_id: str, stop_id: str) -> int | None:
        stmt = select(RouteStopORM.sequence_number).where(
            RouteStopORM.route_variant_id == route_variant_id,
            RouteStopORM.stop_id == stop_id
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_route(self, route: RouteORM) -> RouteORM:
        self.session.add(route)
        self.session.commit()
        self.session.refresh(route)
        return route

    def create_variant(self, variant: RouteVariantORM) -> RouteVariantORM:
        self.session.add(variant)
        self.session.commit()
        self.session.refresh(variant)
        return variant

    def create_route_stop(self, route_stop: RouteStopORM) -> RouteStopORM:
        self.session.add(route_stop)
        self.session.commit()
        self.session.refresh(route_stop)
        return route_stop
