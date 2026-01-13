"""Template model for storing IRB form templates."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Template(Base):
    """
    Template model representing an IRB form template.
    
    Stores the original DOCX file path and the extracted schema
    with sections, fields, anchors, and conditional rules.
    """
    
    __tablename__ = "templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    
    # Original template file
    original_file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Extracted template schema (sections, fields, anchors, rules)
    schema: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Template metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        onupdate=datetime.utcnow,
        nullable=True
    )
    
    # Relationships
    form_instances: Mapped[List["FormInstance"]] = relationship(
        "FormInstance", 
        back_populates="template"
    )
    
    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name='{self.name}', version='{self.version}')>"
    
    @property
    def sections(self) -> List[Dict[str, Any]]:
        """Get sections from schema."""
        return self.schema.get("sections", [])
    
    @property
    def fields(self) -> List[Dict[str, Any]]:
        """Get fields from schema."""
        return self.schema.get("fields", [])
    
    @property
    def rules(self) -> List[Dict[str, Any]]:
        """Get conditional rules from schema."""
        return self.schema.get("rules", [])
