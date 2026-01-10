"""Audit trail Pydantic schemas."""

from datetime import datetime
from typing import Optional, Any, List

from pydantic import BaseModel


class ChangeEventResponse(BaseModel):
    """Schema for change event responses."""
    id: int
    form_instance_id: int
    version_id: Optional[int]
    user_id: int
    user_name: Optional[str] = None
    field_id: str
    field_label: Optional[str]
    old_value: Optional[Any]
    new_value: Optional[Any]
    action_type: Optional[str]
    action_details: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Schema for paginated audit log responses."""
    items: List[ChangeEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
