"""
Admin router for user management (admin-only operations).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from models.base import get_db
from models.user import User
from auth.dependencies import get_current_active_user, require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


class UpdateRoleRequest(BaseModel):
    """Schema for updating user role."""
    email: str
    role: str  # 'user', 'auction_manager', or 'admin'


class UserInfo(BaseModel):
    """User info response."""
    id: int
    email: str
    display_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return [
        UserInfo(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            role=u.role,
            is_active=u.is_active
        )
        for u in users
    ]


@router.post("/users/role")
async def update_user_role(
    data: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a user's role (admin only)."""
    valid_roles = ['user', 'auction_manager', 'admin']
    if data.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = data.role
    db.commit()
    
    return {
        "message": f"User role updated to {data.role}",
        "user": UserInfo(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            is_active=user.is_active
        )
    }


@router.post("/promote-self")
async def promote_self_to_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Temporary endpoint to promote current user to admin.
    FOR DEVELOPMENT ONLY - remove in production!
    """
    # Check if there are any admins yet
    admin_count = db.query(User).filter(User.role == 'admin').count()
    
    # Allow self-promotion only if no admins exist OR user is already admin/manager
    if admin_count == 0 or current_user.is_manager():
        current_user.role = 'admin'
        db.commit()
        return {
            "message": "You are now an admin!",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "display_name": current_user.display_name,
                "role": current_user.role
            }
        }
    else:
        raise HTTPException(
            status_code=403,
            detail="Cannot self-promote when admins already exist"
        )
