"""Audit trail model for tracking all changes."""

from datetime import datetime
from typing import Optional, Any

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChangeEvent(Base):
    """
    ChangeEvent is an append-only audit log entry.
    
    Every field change creates a new ChangeEvent record.
    This allows complete reconstruction of form state at any point in time.
    """
    
    __tablename__ = "change_events"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Form instance reference
    form_instance_id: Mapped[int] = mapped_column(
        ForeignKey("form_instances.id"), 
        nullable=False,
        index=True
    )
    
    # Version reference (which version this change belongs to)
    version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("form_versions.id"), 
        nullable=True,
        index=True
    )
    
    # User who made the change
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False,
        index=True
    )
    
    # Field identification
    field_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    field_label: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Change details
    old_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    
    # Action type for non-field changes
    action_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp (immutable)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # IP address and user agent for additional audit info
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Relationships
    form_instance: Mapped["FormInstance"] = relationship("FormInstance")
    version: Mapped[Optional["FormVersion"]] = relationship(
        "FormVersion",
        back_populates="change_events"
    )
    user: Mapped["User"] = relationship("User", back_populates="change_events")
    
    def __repr__(self) -> str:
        return f"<ChangeEvent(id={self.id}, field='{self.field_id}', user_id={self.user_id})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "form_instance_id": self.form_instance_id,
            "version_id": self.version_id,
            "user_id": self.user_id,
            "field_id": self.field_id,
            "field_label": self.field_label,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "action_type": self.action_type,
            "action_details": self.action_details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
