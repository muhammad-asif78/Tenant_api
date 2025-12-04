from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new user (only within the same tenant)
    """
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user within the same tenant as the current user
    from app.core.security import get_password_hash

    db_user = UserModel(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        tenant_id=current_user.tenant_id  # Same tenant as the creator
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Retrieve users (only within the same tenant)
    """
    users = db.query(UserModel).filter(
        UserModel.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get a specific user (only within the same tenant)
    """
    db_user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.tenant_id == current_user.tenant_id
    ).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update a user (only within the same tenant)
    """
    db_user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.tenant_id == current_user.tenant_id
    ).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user data
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value is not None:
            # Hash the password before saving
            from app.core.security import get_password_hash
            setattr(db_user, "hashed_password", get_password_hash(value))
        else:
            setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Delete a user (only within the same tenant)
    """
    db_user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.tenant_id == current_user.tenant_id
    ).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"ok": True}