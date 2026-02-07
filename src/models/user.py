"""
User model for authentication and authorization.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .base import Base


class User(Base):
    """
    User model with role-based access control.
    
    Roles:
    - admin: Full access, can create auctions and authorize users
    - auction_manager: Can manage their own auctions
    - user: Can participate in auctions they're authorized for
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    
    # Role: admin, auction_manager, user
    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_admin(self) -> bool:
        return self.role == "admin"
    
    def is_manager(self) -> bool:
        return self.role in ("admin", "auction_manager")
