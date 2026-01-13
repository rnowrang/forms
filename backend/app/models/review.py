"""Review workflow models for comments and actions."""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReviewActionType(str, PyEnum):
    """Types of review actions."""
    SUBMIT_FOR_REVIEW = "submit_for_review"
    REQUEST_CHANGES = "request_changes"
    APPROVE = "approve"
    REJECT = "reject"
    RETURN_TO_DRAFT = "return_to_draft"


class CommentThread(Base):
    """
    CommentThread groups comments on a specific field or section.
    
    Threads can be resolved when the issue is addressed.
    """
    
    __tablename__ = "comment_threads"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Form instance reference
    form_instance_id: Mapped[int] = mapped_column(
        ForeignKey("form_instances.id"), 
        nullable=False,
        index=True
    )
    
    # What the comment is about
    field_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    section_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Thread status
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    form_instance: Mapped["FormInstance"] = relationship(
        "FormInstance",
        back_populates="comment_threads"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="thread",
        order_by="Comment.created_at"
    )
    resolved_by: Mapped[Optional["User"]] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<CommentThread(id={self.id}, field='{self.field_id}', resolved={self.is_resolved})>"


class Comment(Base):
    """Individual comment within a thread."""
    
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Thread reference
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("comment_threads.id"), 
        nullable=False,
        index=True
    )
    
    # Author
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False,
        index=True
    )
    
    # Comment content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        onupdate=datetime.utcnow,
        nullable=True
    )
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    thread: Mapped["CommentThread"] = relationship(
        "CommentThread",
        back_populates="comments"
    )
    author: Mapped["User"] = relationship("User", back_populates="comments")
    
    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, thread_id={self.thread_id}, author_id={self.author_id})>"


class ReviewAction(Base):
    """
    ReviewAction tracks workflow state changes.
    
    Records when forms are submitted, approved, returned for changes, etc.
    """
    
    __tablename__ = "review_actions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Form instance reference
    form_instance_id: Mapped[int] = mapped_column(
        ForeignKey("form_instances.id"), 
        nullable=False,
        index=True
    )
    
    # Version reference (which version this action applies to)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("form_versions.id"), 
        nullable=False,
        index=True
    )
    
    # Who performed the action
    performed_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False,
        index=True
    )
    
    # Action details
    action_type: Mapped[ReviewActionType] = mapped_column(
        Enum('submit_for_review', 'request_changes', 'approve', 'reject', 'return_to_draft', name='reviewactiontype', create_type=False),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    form_instance: Mapped["FormInstance"] = relationship("FormInstance")
    version: Mapped["FormVersion"] = relationship("FormVersion")
    performed_by: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<ReviewAction(id={self.id}, type='{self.action_type}', form_id={self.form_instance_id})>"
