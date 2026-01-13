"""Form instance service for CRUD operations and versioning."""

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.form import FormInstance, FormVersion, FormData, FormStatus
from app.models.template import Template
from app.models.user import User
from app.models.audit import ChangeEvent
from app.schemas.form import FormInstanceCreate, FormInstanceUpdate, FieldChange


class FormService:
    """Service for form instance operations."""
    
    @staticmethod
    def get_form_instance(
        db: Session, 
        form_id: int,
        include_data: bool = True
    ) -> Optional[FormInstance]:
        """Get a form instance by ID."""
        query = db.query(FormInstance).filter(FormInstance.id == form_id)
        if include_data:
            query = query.options(
                joinedload(FormInstance.current_data),
                joinedload(FormInstance.template),
                joinedload(FormInstance.owner)
            )
        return query.first()
    
    @staticmethod
    def get_user_forms(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[FormStatus] = None
    ) -> List[FormInstance]:
        """Get all forms for a user."""
        query = db.query(FormInstance).filter(FormInstance.owner_id == user_id)
        if status_filter:
            query = query.filter(FormInstance.status == status_filter)
        return query.options(
            joinedload(FormInstance.template),
            joinedload(FormInstance.owner)
        ).order_by(FormInstance.updated_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_all_forms(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[FormStatus] = None
    ) -> List[FormInstance]:
        """Get all forms (for admin/reviewer)."""
        query = db.query(FormInstance)
        if status_filter:
            query = query.filter(FormInstance.status == status_filter)
        return query.options(
            joinedload(FormInstance.template),
            joinedload(FormInstance.owner)
        ).order_by(FormInstance.updated_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_form_instance(
        db: Session,
        user: User,
        form_data: FormInstanceCreate
    ) -> FormInstance:
        """Create a new form instance."""
        # Verify template exists and is published
        template = db.query(Template).filter(
            Template.id == form_data.template_id,
            Template.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Create form instance
        db_form = FormInstance(
            template_id=form_data.template_id,
            owner_id=user.id,
            title=form_data.title,
            status=FormStatus.DRAFT,
            current_version_number=1,
        )
        db.add(db_form)
        db.flush()  # Get the ID
        
        # Create initial empty form data
        db_form_data = FormData(
            form_instance_id=db_form.id,
            data={},
        )
        db.add(db_form_data)
        
        # Create initial version
        db_version = FormVersion(
            form_instance_id=db_form.id,
            version_number=1,
            version_label="Initial draft",
            data_snapshot={},
            status_at_creation=FormStatus.DRAFT,
            created_by_id=user.id,
        )
        db.add(db_version)
        
        # Log creation event
        db_event = ChangeEvent(
            form_instance_id=db_form.id,
            user_id=user.id,
            field_id="_system",
            action_type="create",
            action_details=f"Form created: {form_data.title}",
            new_value={"title": form_data.title, "template_id": form_data.template_id},
        )
        db.add(db_event)
        
        db.commit()
        db.refresh(db_form)
        
        return db_form
    
    @staticmethod
    def update_form_metadata(
        db: Session,
        form_id: int,
        user: User,
        update_data: FormInstanceUpdate
    ) -> Optional[FormInstance]:
        """Update form instance metadata (not field values)."""
        db_form = FormService.get_form_instance(db, form_id, include_data=False)
        if not db_form:
            return None
        
        # Check permissions
        if db_form.owner_id != user.id and user.role not in ["admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this form"
            )
        
        # Check if form is editable
        if db_form.status in [FormStatus.LOCKED, FormStatus.APPROVED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a locked or approved form"
            )
        
        if update_data.title:
            old_title = db_form.title
            db_form.title = update_data.title
            
            # Log the change
            db_event = ChangeEvent(
                form_instance_id=db_form.id,
                user_id=user.id,
                field_id="_title",
                old_value=old_title,
                new_value=update_data.title,
                action_type="update",
            )
            db.add(db_event)
        
        db.commit()
        db.refresh(db_form)
        return db_form
    
    @staticmethod
    def update_form_data(
        db: Session,
        form_id: int,
        user: User,
        changes: List[FieldChange],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> FormData:
        """Update form field values (autosave)."""
        db_form = FormService.get_form_instance(db, form_id)
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check permissions
        if db_form.owner_id != user.id and user.role not in ["admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this form"
            )
        
        # Check if form is editable
        if db_form.status in [FormStatus.LOCKED, FormStatus.APPROVED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a locked or approved form"
            )
        
        # Get or create form data
        form_data = db_form.current_data
        if not form_data:
            form_data = FormData(
                form_instance_id=db_form.id,
                data={},
            )
            db.add(form_data)
        
        # Apply changes and create audit events
        current_data = dict(form_data.data)
        
        for change in changes:
            # Record change event
            db_event = ChangeEvent(
                form_instance_id=form_id,
                user_id=user.id,
                field_id=change.field_id,
                field_label=change.field_label,
                old_value=current_data.get(change.field_id),
                new_value=change.new_value,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(db_event)
            
            # Update data
            current_data[change.field_id] = change.new_value
        
        form_data.data = current_data
        db_form.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(form_data)
        
        return form_data
    
    @staticmethod
    def get_form_data(db: Session, form_id: int) -> Optional[Dict[str, Any]]:
        """Get current form data."""
        form_data = db.query(FormData).filter(FormData.form_instance_id == form_id).first()
        return form_data.data if form_data else {}
    
    @staticmethod
    def create_version(
        db: Session,
        form_id: int,
        user: User,
        version_label: Optional[str] = None
    ) -> FormVersion:
        """Create a new version snapshot."""
        db_form = FormService.get_form_instance(db, form_id)
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check permissions
        if db_form.owner_id != user.id and user.role not in ["admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create version"
            )
        
        # Get current data
        current_data = db_form.current_data.data if db_form.current_data else {}
        
        # Increment version number
        new_version_number = db_form.current_version_number + 1
        db_form.current_version_number = new_version_number
        
        # Create version snapshot
        db_version = FormVersion(
            form_instance_id=form_id,
            version_number=new_version_number,
            version_label=version_label or f"Version {new_version_number}",
            data_snapshot=current_data,
            status_at_creation=db_form.status,
            created_by_id=user.id,
        )
        db.add(db_version)
        
        # Log event
        db_event = ChangeEvent(
            form_instance_id=form_id,
            user_id=user.id,
            field_id="_system",
            action_type="version_create",
            action_details=f"Created version {new_version_number}",
            new_value={"version_number": new_version_number, "label": version_label},
        )
        db.add(db_event)
        
        db.commit()
        db.refresh(db_version)
        
        return db_version
    
    @staticmethod
    def get_versions(db: Session, form_id: int) -> List[FormVersion]:
        """Get all versions for a form."""
        return db.query(FormVersion).filter(
            FormVersion.form_instance_id == form_id
        ).order_by(FormVersion.version_number.desc()).all()
    
    @staticmethod
    def get_version(db: Session, version_id: int) -> Optional[FormVersion]:
        """Get a specific version."""
        return db.query(FormVersion).filter(FormVersion.id == version_id).first()
    
    @staticmethod
    def delete_form_instance(db: Session, form_id: int, user: User) -> bool:
        """Delete a form instance (only drafts can be deleted)."""
        db_form = FormService.get_form_instance(db, form_id, include_data=False)
        if not db_form:
            return False
        
        # Check permissions
        if db_form.owner_id != user.id and user.role not in ["admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this form"
            )
        
        # Only allow deletion of drafts
        if db_form.status != FormStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft forms can be deleted"
            )
        
        # Delete related records
        db.query(ChangeEvent).filter(ChangeEvent.form_instance_id == form_id).delete()
        db.query(FormVersion).filter(FormVersion.form_instance_id == form_id).delete()
        db.query(FormData).filter(FormData.form_instance_id == form_id).delete()
        db.delete(db_form)
        
        db.commit()
        return True
