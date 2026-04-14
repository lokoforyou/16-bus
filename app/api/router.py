from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bookings,
    compliance,
    driver_ops,
    drivers,
    marshal_ops,
    organizations,
    passengers,
    payments,
    realtime,
    routes,
    trips,
    vehicles,
)

api_router = APIRouter()
v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth.router)
v1_router.include_router(passengers.router)
v1_router.include_router(routes.router)
v1_router.include_router(trips.router)
v1_router.include_router(bookings.router)
v1_router.include_router(payments.router)
v1_router.include_router(driver_ops.router)
v1_router.include_router(drivers.router)
v1_router.include_router(vehicles.router)
v1_router.include_router(marshal_ops.router)
v1_router.include_router(organizations.router)
v1_router.include_router(compliance.router)
v1_router.include_router(realtime.router)

api_router.include_router(v1_router)
