from fastapi import APIRouter, Depends

from app.api.deps import get_application_services
from app.application import ApplicationServices
from app.domain.organizations.schemas import (
    Organization,
    OrganizationCreate,
    OrganizationList,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=Organization)
async def create_organization(
    data: OrganizationCreate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.organizations.create(data)


@router.get("", response_model=OrganizationList)
async def list_organizations(
    services: ApplicationServices = Depends(get_application_services),
) -> OrganizationList:
    return OrganizationList(items=services.organizations.list())


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.organizations.get(organization_id)


@router.patch("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    data: OrganizationUpdate,
    services: ApplicationServices = Depends(get_application_services),
):
    return services.organizations.update(organization_id, data)
