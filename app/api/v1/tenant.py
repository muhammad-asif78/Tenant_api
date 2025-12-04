from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user, get_current_active_superuser
from app.models.tenant import Tenant as TenantModel
from app.models.user import User as UserModel
from app.schemas.tenant import Tenant, TenantCreate, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.post("/", response_model=Tenant, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Create a new tenant (superuser only)
    """
    db_tenant = db.query(TenantModel).filter(TenantModel.name == tenant.name).first()
    if db_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant with this name already exists"
        )
    
    db_tenant = TenantModel(name=tenant.name)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.get("/", response_model=List[Tenant])
def read_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Retrieve all tenants (superuser only)
    """
    tenants = db.query(TenantModel).offset(skip).limit(limit).all()
    return tenants

@router.get("/{tenant_id}", response_model=Tenant)
def read_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Get a specific tenant (superuser only)
    """
    db_tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.put("/{tenant_id}", response_model=Tenant)
def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Update a tenant (superuser only)
    """
    db_tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update tenant data
    update_data = tenant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tenant, field, value)
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Delete a tenant (superuser only)
    Note: This should be used with caution as it will delete all associated data
    """
    db_tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # In a real application, you might want to implement soft delete
    # or additional checks before deleting a tenant
    db.delete(db_tenant)
    db.commit()
    return {"ok": True}