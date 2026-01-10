"""Audit trail router."""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.audit import ChangeEventResponse, AuditLogResponse
from app.services.form import FormService
from app.services.audit import AuditService
from app.services.auth import get_current_active_user

router = APIRouter()


@router.get("/form/{form_id}", response_model=AuditLogResponse)
async def get_form_audit_log(
    form_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    field_id: Optional[str] = None,
    user_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit log for a form with optional filters."""
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
            detail="Not authorized to view audit log"
        )
    
    result = AuditService.get_form_audit_log(
        db, form_id, page, page_size, field_id, user_id, from_date, to_date
    )
    
    # Convert to response format
    items = []
    for event in result["items"]:
        items.append(ChangeEventResponse(
            id=event.id,
            form_instance_id=event.form_instance_id,
            version_id=event.version_id,
            user_id=event.user_id,
            user_name=event.user.full_name if event.user else None,
            field_id=event.field_id,
            field_label=event.field_label,
            old_value=event.old_value,
            new_value=event.new_value,
            action_type=event.action_type,
            action_details=event.action_details,
            timestamp=event.timestamp,
        ))
    
    return AuditLogResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/form/{form_id}/field/{field_id}")
async def get_field_history(
    form_id: int,
    field_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get complete history for a specific field."""
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
            detail="Not authorized to view audit log"
        )
    
    events = AuditService.get_field_history(db, form_id, field_id)
    
    return [
        ChangeEventResponse(
            id=event.id,
            form_instance_id=event.form_instance_id,
            version_id=event.version_id,
            user_id=event.user_id,
            user_name=event.user.full_name if event.user else None,
            field_id=event.field_id,
            field_label=event.field_label,
            old_value=event.old_value,
            new_value=event.new_value,
            action_type=event.action_type,
            action_details=event.action_details,
            timestamp=event.timestamp,
        )
        for event in events
    ]


@router.get("/form/{form_id}/summary")
async def get_activity_summary(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get activity summary for a form."""
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
            detail="Not authorized to view audit log"
        )
    
    return AuditService.get_activity_summary(db, form_id)


@router.get("/form/{form_id}/diff")
async def get_version_diff(
    form_id: int,
    from_version_id: int,
    to_version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get diff between two versions."""
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
            detail="Not authorized to view version diff"
        )
    
    changes = AuditService.get_changes_between_versions(db, form_id, from_version_id, to_version_id)
    return {"changes": changes}
