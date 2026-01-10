"""Review workflow Pydantic schemas."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.review import ReviewActionType


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    content: str = Field(..., min_length=1, max_length=10000)
    field_id: Optional[str] = None
    section_id: Optional[str] = None
    thread_id: Optional[int] = None  # If replying to existing thread


class CommentResponse(BaseModel):
    """Schema for comment responses."""
    id: int
    thread_id: int
    author_id: int
    author_name: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_deleted: bool
    
    class Config:
        from_attributes = True


class CommentThreadResponse(BaseModel):
    """Schema for comment thread responses."""
    id: int
    form_instance_id: int
    field_id: Optional[str]
    section_id: Optional[str]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by_id: Optional[int]
    resolved_by_name: Optional[str] = None
    created_at: datetime
    comments: List[CommentResponse] = []
    
    class Config:
        from_attributes = True


class ResolveThreadRequest(BaseModel):
    """Schema for resolving a comment thread."""
    pass  # Just needs the action, no body required


class ReviewActionCreate(BaseModel):
    """Schema for creating a review action."""
    action_type: ReviewActionType
    notes: Optional[str] = Field(None, max_length=5000)


class ReviewActionResponse(BaseModel):
    """Schema for review action responses."""
    id: int
    form_instance_id: int
    version_id: int
    performed_by_id: int
    performed_by_name: Optional[str] = None
    action_type: ReviewActionType
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
