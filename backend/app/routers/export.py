"""Document export router."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.services.form import FormService
from app.services.document import DocumentService
from app.services.auth import get_current_active_user

router = APIRouter()


@router.post("/form/{form_id}/generate")
async def generate_documents(
    form_id: int,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate DOCX and PDF documents for a form."""
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
            detail="Not authorized to generate documents"
        )
    
    docx_path, pdf_path = DocumentService.generate_documents(db, form_id, version_id)
    
    return {
        "message": "Documents generated successfully",
        "docx_path": docx_path,
        "pdf_path": pdf_path,
    }


@router.get("/form/{form_id}/docx")
async def download_docx(
    form_id: int,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download the generated DOCX for a form."""
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
            detail="Not authorized to download documents"
        )
    
    # Check if documents exist, generate if not
    if version_id:
        paths = DocumentService.get_document_paths(db, form_id, version_id)
        if paths:
            docx_path = paths[0]
        else:
            docx_path, _ = DocumentService.generate_documents(db, form_id, version_id)
    else:
        docx_path, _ = DocumentService.generate_documents(db, form_id)
    
    if not os.path.exists(docx_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    filename = f"form_{form_id}_v{version_id or 'current'}.docx"
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )


@router.get("/form/{form_id}/pdf")
async def download_pdf(
    form_id: int,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download the generated PDF for a form."""
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
            detail="Not authorized to download documents"
        )
    
    # Check if documents exist, generate if not
    if version_id:
        paths = DocumentService.get_document_paths(db, form_id, version_id)
        if paths:
            pdf_path = paths[1]
        else:
            _, pdf_path = DocumentService.generate_documents(db, form_id, version_id)
    else:
        _, pdf_path = DocumentService.generate_documents(db, form_id)
    
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    filename = f"form_{form_id}_v{version_id or 'current'}.pdf"
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename
    )


@router.get("/version/{version_id}/docx")
async def download_version_docx(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download DOCX for a specific version."""
    version = FormService.get_version(db, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return await download_docx(version.form_instance_id, version_id, db, current_user)


@router.get("/version/{version_id}/pdf")
async def download_version_pdf(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download PDF for a specific version."""
    version = FormService.get_version(db, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return await download_pdf(version.form_instance_id, version_id, db, current_user)
