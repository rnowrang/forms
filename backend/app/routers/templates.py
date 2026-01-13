"""Template management router."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
)
from app.services.template import TemplateService
from app.services.auth import get_current_active_user, require_role

router = APIRouter()


@router.get("", response_model=List[TemplateListResponse])
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all templates."""
    templates = TemplateService.get_templates(db, skip, limit, active_only)
    return templates


@router.get("/published", response_model=List[TemplateListResponse])
async def list_published_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all published templates available for form creation."""
    templates = TemplateService.get_published_templates(db)
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a template by ID."""
    template = TemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.post("", response_model=TemplateResponse)
async def create_template(
    name: str = Form(...),
    description: str = Form(None),
    version: str = Form("1.0"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Upload a new template (admin only)."""
    template_data = TemplateCreate(
        name=name,
        description=description,
        version=version
    )
    template = await TemplateService.create_template(db, template_data, file)
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update a template (admin only)."""
    template = TemplateService.update_template(db, template_id, template_data)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Delete (deactivate) a template (admin only)."""
    success = TemplateService.delete_template(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return {"message": "Template deleted successfully"}


@router.post("/{template_id}/publish")
async def publish_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Publish a template for use (admin only)."""
    template = TemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    template.is_published = True
    db.commit()
    
    return {"message": "Template published successfully"}


@router.post("/{template_id}/unpublish")
async def unpublish_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Unpublish a template (admin only)."""
    template = TemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    template.is_published = False
    db.commit()
    
    return {"message": "Template unpublished successfully"}
