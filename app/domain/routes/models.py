from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RouteORM(Base):
    __tablename__ = "routes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    direction: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    variants: Mapped[list["RouteVariantORM"]] = relationship(back_populates="route")


class RouteVariantORM(Base):
    __tablename__ = "route_variants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    route_id: Mapped[str] = mapped_column(ForeignKey("routes.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    route: Mapped["RouteORM"] = relationship(back_populates="variants")
    route_stops: Mapped[list["RouteStopORM"]] = relationship(back_populates="route_variant")


class StopORM(Base):
    __tablename__ = "stops"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    cash_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    route_stops: Mapped[list["RouteStopORM"]] = relationship(back_populates="stop")


class RouteStopORM(Base):
    __tablename__ = "route_stops"
    __table_args__ = (
        UniqueConstraint("route_variant_id", "sequence_number", name="uq_route_stops_variant_sequence"),
        UniqueConstraint("route_variant_id", "stop_id", name="uq_route_stops_variant_stop"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    route_variant_id: Mapped[str] = mapped_column(
        ForeignKey("route_variants.id"), nullable=False, index=True
    )
    stop_id: Mapped[str] = mapped_column(ForeignKey("stops.id"), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    dwell_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

    route_variant: Mapped["RouteVariantORM"] = relationship(back_populates="route_stops")
    stop: Mapped["StopORM"] = relationship(back_populates="route_stops")
