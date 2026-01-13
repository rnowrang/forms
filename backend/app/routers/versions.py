"""Version management router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.form import FormVersionResponse, FormVersionCreate
from app.services.form import FormService
from app.services.auth import get_current_active_user

router = APIRouter()


@router.get("/form/{form_id}", response_model=List[FormVersionResponse])
async def list_form_versions(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all versions for a form."""
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
    
    versions = FormService.get_versions(db, form_id)
    
    result = []
    for v in versions:
        result.append(FormVersionResponse(
            id=v.id,
            form_instance_id=v.form_instance_id,
            version_number=v.version_number,
            version_label=v.version_label,
            data_snapshot=v.data_snapshot,
            status_at_creation=v.status_at_creation,
            generated_docx_path=v.generated_docx_path,
            generated_pdf_path=v.generated_pdf_path,
            created_at=v.created_at,
            created_by_id=v.created_by_id,
            created_by_name=v.created_by.full_name if v.created_by else None,
        ))
    
    return result


@router.get("/{version_id}", response_model=FormVersionResponse)
async def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific version by ID."""
    version = FormService.get_version(db, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Check access via form
    form = FormService.get_form_instance(db, version.form_instance_id, include_data=False)
    if form.owner_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this version"
        )
    
    return FormVersionResponse(
        id=version.id,
        form_instance_id=version.form_instance_id,
        version_number=version.version_number,
        version_label=version.version_label,
        data_snapshot=version.data_snapshot,
        status_at_creation=version.status_at_creation,
        generated_docx_path=version.generated_docx_path,
        generated_pdf_path=version.generated_pdf_path,
        created_at=version.created_at,
        created_by_id=version.created_by_id,
        created_by_name=version.created_by.full_name if version.created_by else None,
    )


@router.post("/form/{form_id}", response_model=FormVersionResponse)
async def create_version(
    form_id: int,
    version_data: Optional[FormVersionCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new version snapshot for a form."""
    version_label = version_data.version_label if version_data else None
    version = FormService.create_version(db, form_id, current_user, version_label)
    
    return FormVersionResponse(
        id=version.id,
        form_instance_id=version.form_instance_id,
        version_number=version.version_number,
        version_label=version.version_label,
        data_snapshot=version.data_snapshot,
        status_at_creation=version.status_at_creation,
        generated_docx_path=version.generated_docx_path,
        generated_pdf_path=version.generated_pdf_path,
        created_at=version.created_at,
        created_by_id=version.created_by_id,
        created_by_name=version.created_by.full_name if version.created_by else None,
    )
