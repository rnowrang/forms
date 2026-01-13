"""Review workflow router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.review import (
    CommentCreate,
    CommentResponse,
    CommentThreadResponse,
    ReviewActionCreate,
    ReviewActionResponse,
)
from app.services.form import FormService
from app.services.review import ReviewService
from app.services.auth import get_current_active_user, require_role

router = APIRouter()


# Workflow actions
@router.post("/form/{form_id}/submit")
async def submit_for_review(
    form_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit a form for review."""
    form = ReviewService.submit_for_review(db, form_id, current_user, notes)
    status = form.status.value if hasattr(form.status, 'value') else form.status
    return {"message": "Form submitted for review", "status": status}


@router.post("/form/{form_id}/request-changes")
async def request_changes(
    form_id: int,
    action: ReviewActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN))
):
    """Request changes on a submitted form (reviewer only)."""
    form = ReviewService.request_changes(db, form_id, current_user, action.notes)
    status = form.status.value if hasattr(form.status, 'value') else form.status
    return {"message": "Changes requested", "status": status}


@router.post("/form/{form_id}/approve")
async def approve_form(
    form_id: int,
    action: Optional[ReviewActionCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN))
):
    """Approve a form (reviewer only)."""
    notes = action.notes if action else None
    form = ReviewService.approve_form(db, form_id, current_user, notes)
    status = form.status.value if hasattr(form.status, 'value') else form.status
    return {"message": "Form approved", "status": status}


@router.post("/form/{form_id}/return-to-draft")
async def return_to_draft(
    form_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Return a form to draft status."""
    form = ReviewService.return_to_draft(db, form_id, current_user, notes)
    status = form.status.value if hasattr(form.status, 'value') else form.status
    return {"message": "Form returned to draft", "status": status}


# Comments
@router.get("/form/{form_id}/comments", response_model=List[CommentThreadResponse])
async def get_form_comments(
    form_id: int,
    include_resolved: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all comment threads for a form."""
    # Check form access
    form = FormService.get_form_instance(db, form_id, include_data=False)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    if form.owner_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view comments"
        )
    
    threads = ReviewService.get_form_comments(db, form_id, include_resolved)
    
    result = []
    for thread in threads:
        comments = [
            CommentResponse(
                id=c.id,
                thread_id=c.thread_id,
                author_id=c.author_id,
                author_name=c.author.full_name if c.author else None,
                content=c.content,
                created_at=c.created_at,
                updated_at=c.updated_at,
                is_deleted=c.is_deleted,
            )
            for c in thread.comments if not c.is_deleted
        ]
        
        result.append(CommentThreadResponse(
            id=thread.id,
            form_instance_id=thread.form_instance_id,
            field_id=thread.field_id,
            section_id=thread.section_id,
            is_resolved=thread.is_resolved,
            resolved_at=thread.resolved_at,
            resolved_by_id=thread.resolved_by_id,
            resolved_by_name=thread.resolved_by.full_name if thread.resolved_by else None,
            created_at=thread.created_at,
            comments=comments,
        ))
    
    return result


@router.post("/form/{form_id}/comments", response_model=CommentResponse)
async def create_comment(
    form_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a comment on a form field or section."""
    comment = ReviewService.create_comment(
        db,
        form_id,
        current_user,
        comment_data.content,
        comment_data.field_id,
        comment_data.section_id,
        comment_data.thread_id,
    )
    
    return CommentResponse(
        id=comment.id,
        thread_id=comment.thread_id,
        author_id=comment.author_id,
        author_name=current_user.full_name,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_deleted=comment.is_deleted,
    )


@router.post("/threads/{thread_id}/resolve")
async def resolve_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Resolve a comment thread."""
    thread = ReviewService.resolve_thread(db, thread_id, current_user)
    return {"message": "Thread resolved", "thread_id": thread.id}


# Review history
@router.get("/form/{form_id}/history", response_model=List[ReviewActionResponse])
async def get_review_history(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get review action history for a form."""
    # Check form access
    form = FormService.get_form_instance(db, form_id, include_data=False)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    if form.owner_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view review history"
        )
    
    actions = ReviewService.get_review_history(db, form_id)
    
    return [
        ReviewActionResponse(
            id=action.id,
            form_instance_id=action.form_instance_id,
            version_id=action.version_id,
            performed_by_id=action.performed_by_id,
            performed_by_name=action.performed_by.full_name if action.performed_by else None,
            action_type=action.action_type,
            notes=action.notes,
            created_at=action.created_at,
        )
        for action in actions
    ]
