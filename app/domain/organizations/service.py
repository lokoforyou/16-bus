from typing import List
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.organizations.models import OrganizationORM
from app.domain.organizations.repository import OrganizationRepository
from app.domain.organizations.schemas import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    def __init__(self, repository: OrganizationRepository):
        self.repository = repository

    def create_organization(self, data: OrganizationCreate) -> OrganizationORM:
        existing = self.repository.get_by_name(data.name)
        if existing:
            raise ConflictError(f"Organization with name {data.name} already exists")

        org = OrganizationORM(
            name=data.name,
            type=data.type,
            compliance_status=data.compliance_status,
            is_active=data.is_active
        )
        return self.repository.create(org)

    def get_organization(self, org_id: str) -> OrganizationORM:
        org = self.repository.get_by_id(org_id)
        if not org:
            raise NotFoundError("Organization not found")
        return org

    def list_organizations(self) -> List[OrganizationORM]:
        return self.repository.list()

    def update_organization(self, org_id: str, data: OrganizationUpdate) -> OrganizationORM:
        org = self.get_organization(org_id)
        
        if data.name is not None:
            existing = self.repository.get_by_name(data.name)
            if existing and existing.id != org_id:
                raise ConflictError(f"Organization with name {data.name} already exists")
            org.name = data.name
        
        if data.type is not None:
            org.type = data.type
        if data.compliance_status is not None:
            org.compliance_status = data.compliance_status
        if data.is_active is not None:
            org.is_active = data.is_active
            
        return self.repository.update(org)

    def delete_organization(self, org_id: str) -> None:
        org = self.get_organization(org_id)
        self.repository.delete(org)
