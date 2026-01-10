"""Review workflow service for comments and state transitions."""

from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.form import FormInstance, FormVersion, FormStatus
from app.models.review import CommentThread, Comment, ReviewAction, ReviewActionType
from app.models.user import User, UserRole
from app.models.audit import ChangeEvent


class ReviewService:
    """Service for review workflow operations."""
    
    # Valid state transitions
    TRANSITIONS = {
        FormStatus.DRAFT: [FormStatus.IN_REVIEW],
        FormStatus.IN_REVIEW: [FormStatus.NEEDS_CHANGES, FormStatus.APPROVED, FormStatus.DRAFT],
        FormStatus.NEEDS_CHANGES: [FormStatus.IN_REVIEW, FormStatus.DRAFT],
        FormStatus.APPROVED: [FormStatus.LOCKED],
        FormStatus.LOCKED: [],  # Terminal state
    }
    
    @staticmethod
    def submit_for_review(
        db: Session,
        form_id: int,
        user: User,
        notes: Optional[str] = None
    ) -> FormInstance:
        """Submit a form for review."""
        db_form = db.query(FormInstance).options(
            joinedload(FormInstance.current_data)
        ).filter(FormInstance.id == form_id).first()
        
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check permissions
        if db_form.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can submit for review"
            )
        
        # Validate transition
        if FormStatus.IN_REVIEW not in ReviewService.TRANSITIONS.get(db_form.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit for review from status: {db_form.status}"
            )
        
        # Create a new version for submission
        current_data = db_form.current_data.data if db_form.current_data else {}
        new_version_number = db_form.current_version_number + 1
        
        db_version = FormVersion(
            form_instance_id=form_id,
            version_number=new_version_number,
            version_label=f"Submitted v{new_version_number}",
            data_snapshot=current_data,
            status_at_creation=FormStatus.IN_REVIEW,
            created_by_id=user.id,
        )
        db.add(db_version)
        db.flush()
        
        # Update form status
        db_form.status = FormStatus.IN_REVIEW
        db_form.current_version_number = new_version_number
        db_form.submitted_at = datetime.utcnow()
        
        # Create review action
        db_action = ReviewAction(
            form_instance_id=form_id,
            version_id=db_version.id,
            performed_by_id=user.id,
            action_type=ReviewActionType.SUBMIT_FOR_REVIEW,
            notes=notes,
        )
        db.add(db_action)
        
        # Log event
        db_event = ChangeEvent(
            form_instance_id=form_id,
            version_id=db_version.id,
            user_id=user.id,
            field_id="_system",
            action_type="submit_for_review",
            action_details=f"Submitted for review - Version {new_version_number}",
        )
        db.add(db_event)
        
        db.commit()
        db.refresh(db_form)
        
        return db_form
    
    @staticmethod
    def request_changes(
        db: Session,
        form_id: int,
        user: User,
        notes: Optional[str] = None
    ) -> FormInstance:
        """Request changes on a submitted form."""
        db_form = db.query(FormInstance).filter(FormInstance.id == form_id).first()
        
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check permissions (reviewers and admins only)
        if user.role not in [UserRole.REVIEWER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only reviewers can request changes"
            )
        
        # Validate transition
        if FormStatus.NEEDS_CHANGES not in ReviewService.TRANSITIONS.get(db_form.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot request changes from status: {db_form.status}"
            )
        
        # Get current version
        current_version = db.query(FormVersion).filter(
            FormVersion.form_instance_id == form_id,
            FormVersion.version_number == db_form.current_version_number
        ).first()
        
        # Update status
        db_form.status = FormStatus.NEEDS_CHANGES
        
        # Create review action
        db_action = ReviewAction(
            form_instance_id=form_id,
            version_id=current_version.id if current_version else None,
            performed_by_id=user.id,
            action_type=ReviewActionType.REQUEST_CHANGES,
            notes=notes,
        )
        db.add(db_action)
        
        # Log event
        db_event = ChangeEvent(
            form_instance_id=form_id,
            user_id=user.id,
            field_id="_system",
            action_type="request_changes",
            action_details=notes or "Changes requested",
        )
        db.add(db_event)
        
        db.commit()
        db.refresh(db_form)
        
        return db_form
    
    @staticmethod
    def approve_form(
        db: Session,
        form_id: int,
        user: User,
        notes: Optional[str] = None
    ) -> FormInstance:
        """Approve a form."""
        db_form = db.query(FormInstance).filter(FormInstance.id == form_id).first()
        
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check permissions
        if user.role not in [UserRole.REVIEWER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only reviewers can approve forms"
            )
        
        # Validate transition
        if FormStatus.APPROVED not in ReviewService.TRANSITIONS.get(db_form.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve from status: {db_form.status}"
            )
        
        # Get current version
        current_version = db.query(FormVersion).filter(
            FormVersion.form_instance_id == form_id,
            FormVersion.version_number == db_form.current_version_number
        ).first()
        
        # Update status
        db_form.status = FormStatus.APPROVED
        
        # Create review action
        db_action = ReviewAction(
            form_instance_id=form_id,
            version_id=current_version.id if current_version else None,
            performed_by_id=user.id,
            action_type=ReviewActionType.APPROVE,
            notes=notes,
        )
        db.add(db_action)
        
        # Log event
        db_event = ChangeEvent(
            form_instance_id=form_id,
            user_id=user.id,
            field_id="_system",
            action_type="approve",
            action_details=notes or "Form approved",
        )
        db.add(db_event)
        
        db.commit()
        db.refresh(db_form)
        
        return db_form
    
    @staticmethod
    def return_to_draft(
        db: Session,
        form_id: int,
        user: User,
        notes: Optional[str] = None
    ) -> FormInstance:
        """Return a form to draft status."""
        db_form = db.query(FormInstance).filter(FormInstance.id == form_id).first()
        
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check permissions (owner or reviewer/admin)
        if db_form.owner_id != user.id and user.role not in [UserRole.REVIEWER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to return this form to draft"
            )
        
        # Validate transition
        if FormStatus.DRAFT not in ReviewService.TRANSITIONS.get(db_form.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot return to draft from status: {db_form.status}"
            )
        
        # Update status
        db_form.status = FormStatus.DRAFT
        
        # Log event
        db_event = ChangeEvent(
            form_instance_id=form_id,
            user_id=user.id,
            field_id="_system",
            action_type="return_to_draft",
            action_details=notes or "Returned to draft",
        )
        db.add(db_event)
        
        db.commit()
        db.refresh(db_form)
        
        return db_form
    
    # Comment operations
    @staticmethod
    def create_comment(
        db: Session,
        form_id: int,
        user: User,
        content: str,
        field_id: Optional[str] = None,
        section_id: Optional[str] = None,
        thread_id: Optional[int] = None
    ) -> Comment:
        """Create a comment on a form field or section."""
        # Verify form exists
        db_form = db.query(FormInstance).filter(FormInstance.id == form_id).first()
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Get or create thread
        if thread_id:
            thread = db.query(CommentThread).filter(
                CommentThread.id == thread_id
            ).first()
            if not thread:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comment thread not found"
                )
        else:
            # Create new thread
            thread = CommentThread(
                form_instance_id=form_id,
                field_id=field_id,
                section_id=section_id,
            )
            db.add(thread)
            db.flush()
        
        # Create comment
        comment = Comment(
            thread_id=thread.id,
            author_id=user.id,
            content=content,
        )
        db.add(comment)
        
        db.commit()
        db.refresh(comment)
        
        return comment
    
    @staticmethod
    def get_form_comments(
        db: Session,
        form_id: int,
        include_resolved: bool = False
    ) -> List[CommentThread]:
        """Get all comment threads for a form."""
        query = db.query(CommentThread).filter(
            CommentThread.form_instance_id == form_id
        )
        
        if not include_resolved:
            query = query.filter(CommentThread.is_resolved == False)
        
        return query.options(
            joinedload(CommentThread.comments).joinedload(Comment.author),
            joinedload(CommentThread.resolved_by)
        ).order_by(CommentThread.created_at.desc()).all()
    
    @staticmethod
    def resolve_thread(
        db: Session,
        thread_id: int,
        user: User
    ) -> CommentThread:
        """Resolve a comment thread."""
        thread = db.query(CommentThread).filter(
            CommentThread.id == thread_id
        ).first()
        
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
        
        thread.is_resolved = True
        thread.resolved_at = datetime.utcnow()
        thread.resolved_by_id = user.id
        
        db.commit()
        db.refresh(thread)
        
        return thread
    
    @staticmethod
    def get_review_history(
        db: Session,
        form_id: int
    ) -> List[ReviewAction]:
        """Get review action history for a form."""
        return db.query(ReviewAction).filter(
            ReviewAction.form_instance_id == form_id
        ).options(
            joinedload(ReviewAction.performed_by),
            joinedload(ReviewAction.version)
        ).order_by(ReviewAction.created_at.desc()).all()
