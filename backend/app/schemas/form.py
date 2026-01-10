"""Form instance and version Pydantic schemas."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field

from app.models.form import FormStatus


class FormInstanceCreate(BaseModel):
    """Schema for creating a new form instance."""
    template_id: int
    title: str = Field(..., min_length=1, max_length=512)


class FormInstanceUpdate(BaseModel):
    """Schema for updating form instance metadata."""
    title: Optional[str] = Field(None, min_length=1, max_length=512)


class FieldChange(BaseModel):
    """Schema for a single field change."""
    field_id: str
    field_label: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Any


class FormDataUpdate(BaseModel):
    """Schema for updating form data (autosave)."""
    changes: List[FieldChange]


class FormVersionCreate(BaseModel):
    """Schema for creating a new version."""
    version_label: Optional[str] = None


class FormInstanceResponse(BaseModel):
    """Schema for form instance responses."""
    id: int
    template_id: int
    owner_id: int
    title: str
    status: FormStatus
    current_version_number: int
    created_at: datetime
    updated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    
    # Nested data
    data: Optional[Dict[str, Any]] = None
    template_name: Optional[str] = None
    owner_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class FormVersionResponse(BaseModel):
    """Schema for form version responses."""
    id: int
    form_instance_id: int
    version_number: int
    version_label: Optional[str]
    data_snapshot: Dict[str, Any]
    status_at_creation: FormStatus
    generated_docx_path: Optional[str]
    generated_pdf_path: Optional[str]
    created_at: datetime
    created_by_id: int
    created_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class FormListResponse(BaseModel):
    """Schema for form list responses."""
    id: int
    template_id: int
    template_name: str
    title: str
    status: FormStatus
    current_version_number: int
    owner_name: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
