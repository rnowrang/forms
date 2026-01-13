"""User model for authentication and authorization."""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, PyEnum):
    """User roles in the system."""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    
    def __str__(self) -> str:
        return self.value


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]), 
        default=UserRole.RESEARCHER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        onupdate=datetime.utcnow,
        nullable=True
    )
    
    # Relationships
    form_instances: Mapped[List["FormInstance"]] = relationship(
        "FormInstance", 
        back_populates="owner",
        foreign_keys="FormInstance.owner_id"
    )
    change_events: Mapped[List["ChangeEvent"]] = relationship(
        "ChangeEvent", 
        back_populates="user"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", 
        back_populates="author"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
