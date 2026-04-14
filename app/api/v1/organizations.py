from fastapi import APIRouter, Depends
from app.api.deps import get_organization_service, get_current_user_token
from app.domain.auth.models import UserRole
from app.domain.auth.permissions import check_org_ownership, check_role
from app.domain.auth.schemas import TokenData
from app.domain.organizations.models import OrganizationORM
from app.domain.organizations.schemas import (
    Organization,
    OrganizationCreate,
    OrganizationList,
    OrganizationUpdate,
)
from app.domain.organizations.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=Organization)
async def create_organization(
    data: OrganizationCreate,
    organization_service: OrganizationService = Depends(get_organization_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> OrganizationORM:
    check_role(token_data, [UserRole.SUPER_ADMIN])
    return organization_service.create_organization(data)


@router.get("", response_model=OrganizationList)
async def list_organizations(
    organization_service: OrganizationService = Depends(get_organization_service),
) -> OrganizationList:
    items = organization_service.list_organizations()
    return OrganizationList(items=items)


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    organization_service: OrganizationService = Depends(get_organization_service),
) -> OrganizationORM:
    return organization_service.get_organization(organization_id)


@router.patch("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    data: OrganizationUpdate,
    organization_service: OrganizationService = Depends(get_organization_service),
    token_data: TokenData = Depends(get_current_user_token),
) -> OrganizationORM:
    check_role(token_data, [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])
    check_org_ownership(token_data, organization_id)
    return organization_service.update_organization(organization_id, data)
