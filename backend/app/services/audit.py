"""Audit service for change tracking and history."""

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.audit import ChangeEvent
from app.models.form import FormVersion


class AuditService:
    """Service for audit trail operations."""
    
    @staticmethod
    def get_form_audit_log(
        db: Session,
        form_id: int,
        page: int = 1,
        page_size: int = 50,
        field_id: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get paginated audit log for a form."""
        query = db.query(ChangeEvent).filter(
            ChangeEvent.form_instance_id == form_id
        )
        
        # Apply filters
        if field_id:
            query = query.filter(ChangeEvent.field_id == field_id)
        if user_id:
            query = query.filter(ChangeEvent.user_id == user_id)
        if from_date:
            query = query.filter(ChangeEvent.timestamp >= from_date)
        if to_date:
            query = query.filter(ChangeEvent.timestamp <= to_date)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        events = query.options(
            joinedload(ChangeEvent.user)
        ).order_by(
            ChangeEvent.timestamp.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "items": events,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    
    @staticmethod
    def get_version_changes(
        db: Session,
        form_id: int,
        version_id: int
    ) -> List[ChangeEvent]:
        """Get changes associated with a specific version."""
        return db.query(ChangeEvent).filter(
            ChangeEvent.form_instance_id == form_id,
            ChangeEvent.version_id == version_id
        ).options(
            joinedload(ChangeEvent.user)
        ).order_by(ChangeEvent.timestamp.asc()).all()
    
    @staticmethod
    def get_field_history(
        db: Session,
        form_id: int,
        field_id: str
    ) -> List[ChangeEvent]:
        """Get the complete history of changes for a specific field."""
        return db.query(ChangeEvent).filter(
            ChangeEvent.form_instance_id == form_id,
            ChangeEvent.field_id == field_id
        ).options(
            joinedload(ChangeEvent.user)
        ).order_by(ChangeEvent.timestamp.asc()).all()
    
    @staticmethod
    def reconstruct_form_state(
        db: Session,
        form_id: int,
        target_timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Reconstruct form state at a specific point in time.
        
        This replays all change events up to the target timestamp.
        """
        # Get all events up to the timestamp
        events = db.query(ChangeEvent).filter(
            ChangeEvent.form_instance_id == form_id,
            ChangeEvent.timestamp <= target_timestamp,
            ChangeEvent.field_id != "_system"  # Exclude system events
        ).order_by(ChangeEvent.timestamp.asc()).all()
        
        # Replay events to build state
        state = {}
        for event in events:
            if event.new_value is not None:
                state[event.field_id] = event.new_value
            elif event.field_id in state:
                del state[event.field_id]
        
        return state
    
    @staticmethod
    def get_changes_between_versions(
        db: Session,
        form_id: int,
        from_version_id: int,
        to_version_id: int
    ) -> List[Dict[str, Any]]:
        """Get the diff between two versions."""
        # Get both versions
        from_version = db.query(FormVersion).filter(
            FormVersion.id == from_version_id
        ).first()
        to_version = db.query(FormVersion).filter(
            FormVersion.id == to_version_id
        ).first()
        
        if not from_version or not to_version:
            return []
        
        from_data = from_version.data_snapshot or {}
        to_data = to_version.data_snapshot or {}
        
        # Build diff
        changes = []
        all_keys = set(from_data.keys()) | set(to_data.keys())
        
        for key in all_keys:
            old_val = from_data.get(key)
            new_val = to_data.get(key)
            
            if old_val != new_val:
                changes.append({
                    "field_id": key,
                    "old_value": old_val,
                    "new_value": new_val,
                    "change_type": "added" if old_val is None else (
                        "removed" if new_val is None else "modified"
                    ),
                })
        
        return changes
    
    @staticmethod
    def get_activity_summary(
        db: Session,
        form_id: int
    ) -> Dict[str, Any]:
        """Get activity summary for a form."""
        # Count by user
        user_counts = db.query(
            ChangeEvent.user_id,
            func.count(ChangeEvent.id).label('count')
        ).filter(
            ChangeEvent.form_instance_id == form_id
        ).group_by(ChangeEvent.user_id).all()
        
        # Count by field
        field_counts = db.query(
            ChangeEvent.field_id,
            func.count(ChangeEvent.id).label('count')
        ).filter(
            ChangeEvent.form_instance_id == form_id,
            ChangeEvent.field_id != "_system"
        ).group_by(ChangeEvent.field_id).order_by(
            func.count(ChangeEvent.id).desc()
        ).limit(10).all()
        
        # Get date range
        first_event = db.query(ChangeEvent).filter(
            ChangeEvent.form_instance_id == form_id
        ).order_by(ChangeEvent.timestamp.asc()).first()
        
        last_event = db.query(ChangeEvent).filter(
            ChangeEvent.form_instance_id == form_id
        ).order_by(ChangeEvent.timestamp.desc()).first()
        
        return {
            "total_changes": sum(c[1] for c in user_counts),
            "changes_by_user": [{"user_id": c[0], "count": c[1]} for c in user_counts],
            "most_edited_fields": [{"field_id": c[0], "count": c[1]} for c in field_counts],
            "first_activity": first_event.timestamp.isoformat() if first_event else None,
            "last_activity": last_event.timestamp.isoformat() if last_event else None,
        }
