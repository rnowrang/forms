"""Form instance and version models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FormStatus(str, PyEnum):
    """Form instance workflow states."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    NEEDS_CHANGES = "needs_changes"
    APPROVED = "approved"
    LOCKED = "locked"


class FormInstance(Base):
    """
    FormInstance represents a specific IRB submission.
    
    Each form instance is based on a template and belongs to a user.
    It tracks the current status and references all versions.
    """
    
    __tablename__ = "form_instances"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Template reference
    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id"), 
        nullable=False,
        index=True
    )
    
    # Owner (submitter)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False,
        index=True
    )
    
    # Form metadata
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[FormStatus] = mapped_column(
        Enum(FormStatus), 
        default=FormStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Current version number
    current_version_number: Mapped[int] = mapped_column(Integer, default=1)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        onupdate=datetime.utcnow,
        nullable=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    template: Mapped["Template"] = relationship("Template", back_populates="form_instances")
    owner: Mapped["User"] = relationship(
        "User", 
        back_populates="form_instances",
        foreign_keys=[owner_id]
    )
    versions: Mapped[List["FormVersion"]] = relationship(
        "FormVersion", 
        back_populates="form_instance",
        order_by="FormVersion.version_number"
    )
    current_data: Mapped[Optional["FormData"]] = relationship(
        "FormData",
        back_populates="form_instance",
        uselist=False
    )
    comment_threads: Mapped[List["CommentThread"]] = relationship(
        "CommentThread",
        back_populates="form_instance"
    )
    
    def __repr__(self) -> str:
        return f"<FormInstance(id={self.id}, title='{self.title}', status='{self.status}')>"


class FormVersion(Base):
    """
    FormVersion represents a snapshot of form data at a specific point.
    
    Versions are created when:
    - User explicitly saves a version
    - Form is submitted for review
    - Revisions are submitted after changes requested
    """
    
    __tablename__ = "form_versions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Form instance reference
    form_instance_id: Mapped[int] = mapped_column(
        ForeignKey("form_instances.id"), 
        nullable=False,
        index=True
    )
    
    # Version metadata
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Snapshot of form data at this version
    data_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Status when this version was created
    status_at_creation: Mapped[FormStatus] = mapped_column(
        Enum(FormStatus),
        nullable=False
    )
    
    # Generated documents for this version
    generated_docx_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    generated_pdf_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    form_instance: Mapped["FormInstance"] = relationship(
        "FormInstance", 
        back_populates="versions"
    )
    created_by: Mapped["User"] = relationship("User")
    change_events: Mapped[List["ChangeEvent"]] = relationship(
        "ChangeEvent",
        back_populates="version"
    )
    
    def __repr__(self) -> str:
        return f"<FormVersion(id={self.id}, form_id={self.form_instance_id}, v{self.version_number})>"


class FormData(Base):
    """
    FormData stores the current working state of form field values.
    
    This is the live data that gets updated with each change.
    FormVersion snapshots are created from this data.
    """
    
    __tablename__ = "form_data"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Form instance reference (one-to-one)
    form_instance_id: Mapped[int] = mapped_column(
        ForeignKey("form_instances.id"), 
        unique=True,
        nullable=False,
        index=True
    )
    
    # Current field values as JSON
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Last modified
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationship
    form_instance: Mapped["FormInstance"] = relationship(
        "FormInstance",
        back_populates="current_data"
    )
    
    def __repr__(self) -> str:
        return f"<FormData(form_instance_id={self.form_instance_id})>"
