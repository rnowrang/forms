"""Form instance management router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.form import FormStatus
from app.schemas.form import (
    FormInstanceCreate,
    FormInstanceUpdate,
    FormInstanceResponse,
    FormDataUpdate,
    FormListResponse,
)
from app.services.form import FormService
from app.services.auth import get_current_active_user, require_role

router = APIRouter()


@router.get("", response_model=List[FormListResponse])
async def list_forms(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[FormStatus] = None,
    all_forms: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List forms.
    
    - Regular users see their own forms
    - Admins/reviewers can see all forms with all_forms=true
    """
    if all_forms and current_user.role in [UserRole.ADMIN, UserRole.REVIEWER]:
        forms = FormService.get_all_forms(db, skip, limit, status_filter)
    else:
        forms = FormService.get_user_forms(db, current_user.id, skip, limit, status_filter)
    
    result = []
    for form in forms:
        result.append(FormListResponse(
            id=form.id,
            template_id=form.template_id,
            template_name=form.template.name if form.template else "Unknown",
            title=form.title,
            status=form.status,
            current_version_number=form.current_version_number,
            owner_name=form.owner.full_name if form.owner else "Unknown",
            created_at=form.created_at,
            updated_at=form.updated_at,
        ))
    
    return result


@router.post("", response_model=FormInstanceResponse)
async def create_form(
    form_data: FormInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new form instance."""
    form = FormService.create_form_instance(db, current_user, form_data)
    return FormInstanceResponse(
        id=form.id,
        template_id=form.template_id,
        owner_id=form.owner_id,
        title=form.title,
        status=form.status,
        current_version_number=form.current_version_number,
        created_at=form.created_at,
        updated_at=form.updated_at,
        submitted_at=form.submitted_at,
        data={},
        template_name=form.template.name if form.template else None,
        owner_name=form.owner.full_name if form.owner else None,
    )


@router.get("/{form_id}", response_model=FormInstanceResponse)
async def get_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a form instance by ID."""
    form = FormService.get_form_instance(db, form_id)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    # Check access permissions
    if form.owner_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this form"
        )
    
    return FormInstanceResponse(
        id=form.id,
        template_id=form.template_id,
        owner_id=form.owner_id,
        title=form.title,
        status=form.status,
        current_version_number=form.current_version_number,
        created_at=form.created_at,
        updated_at=form.updated_at,
        submitted_at=form.submitted_at,
        data=form.current_data.data if form.current_data else {},
        template_name=form.template.name if form.template else None,
        owner_name=form.owner.full_name if form.owner else None,
    )


@router.put("/{form_id}", response_model=FormInstanceResponse)
async def update_form_metadata(
    form_id: int,
    update_data: FormInstanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update form instance metadata (title, etc.)."""
    form = FormService.update_form_metadata(db, form_id, current_user, update_data)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    return form


@router.post("/{form_id}/data")
async def update_form_data(
    form_id: int,
    data_update: FormDataUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update form field values (autosave endpoint)."""
    # Get client info for audit
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    form_data = FormService.update_form_data(
        db, form_id, current_user, data_update.changes, ip_address, user_agent
    )
    
    return {"message": "Form data updated", "data": form_data.data}


@router.get("/{form_id}/data")
async def get_form_data(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current form data."""
    form = FormService.get_form_instance(db, form_id, include_data=False)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    # Check access
    if form.owner_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this form"
        )
    
    data = FormService.get_form_data(db, form_id)
    return {"data": data}


@router.delete("/{form_id}")
async def delete_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a form instance (draft only)."""
    success = FormService.delete_form_instance(db, form_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    return {"message": "Form deleted successfully"}
