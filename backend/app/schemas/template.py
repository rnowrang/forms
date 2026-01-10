"""Template-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class FieldAnchor(BaseModel):
    """Anchor information for locating where to write values in DOCX."""
    type: str = Field(..., description="Anchor type: 'label', 'table_cell', 'paragraph', 'bookmark'")
    label_text: Optional[str] = Field(None, description="Text of nearby label to anchor to")
    table_header: Optional[str] = Field(None, description="Table header text for table cell anchors")
    row_index: Optional[int] = Field(None, description="Row index in table (0-based)")
    column_index: Optional[int] = Field(None, description="Column index in table (0-based)")
    paragraph_contains: Optional[str] = Field(None, description="Text that the target paragraph contains")
    offset: Optional[int] = Field(0, description="Character offset from anchor position")


class TemplateSchemaField(BaseModel):
    """Schema for a single form field in the template."""
    id: str = Field(..., description="Unique stable field identifier (e.g., 'study.title')")
    type: str = Field(..., description="Field type: text, textarea, checkbox, radio, select, date, email, phone, repeatable")
    label: str = Field(..., description="Human-readable field label")
    section_id: str = Field(..., description="ID of the section this field belongs to")
    required: bool = False
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    default_value: Optional[Any] = None
    options: Optional[List[Dict[str, str]]] = Field(None, description="Options for select/radio/checkbox fields")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation rules (min, max, pattern, etc.)")
    anchor: Optional[FieldAnchor] = Field(None, description="DOCX anchor for this field")
    repeatable_config: Optional[Dict[str, Any]] = Field(None, description="Config for repeatable fields (min, max rows)")


class TemplateSchemaSection(BaseModel):
    """Schema for a form section."""
    id: str = Field(..., description="Unique section identifier (e.g., 'sec_I')")
    title: str = Field(..., description="Section title (e.g., 'I. Study Personnel')")
    description: Optional[str] = None
    order: int = Field(..., description="Display order")
    collapsible: bool = True
    collapsed_by_default: bool = False


class RuleCondition(BaseModel):
    """Condition for a conditional rule."""
    field: str = Field(..., description="Field ID to check")
    operator: str = Field(..., description="Operator: equals, not_equals, contains, not_contains, is_empty, is_not_empty")
    value: Optional[Any] = None


class RuleAction(BaseModel):
    """Action to take when rule condition is met."""
    action: str = Field(..., description="Action: show, hide, require, optional, clear, set_value")
    field: str = Field(..., description="Target field ID")
    value: Optional[Any] = Field(None, description="Value to set (for set_value action)")


class TemplateSchemaRule(BaseModel):
    """Conditional logic rule."""
    id: str = Field(..., description="Unique rule identifier")
    conditions: List[RuleCondition] = Field(..., description="Conditions (AND logic)")
    then_actions: List[RuleAction] = Field(..., description="Actions when conditions are true")
    else_actions: Optional[List[RuleAction]] = Field(None, description="Actions when conditions are false")


class TemplateSchema(BaseModel):
    """Complete template schema."""
    sections: List[TemplateSchemaSection] = []
    fields: List[TemplateSchemaField] = []
    rules: List[TemplateSchemaRule] = []


class TemplateCreate(BaseModel):
    """Schema for creating a new template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    version: str = "1.0"


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = None
    schema: Optional[TemplateSchema] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Schema for template responses."""
    id: int
    name: str
    description: Optional[str]
    version: str
    original_file_name: str
    schema: Dict[str, Any]
    is_active: bool
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Schema for template list responses."""
    id: int
    name: str
    description: Optional[str]
    version: str
    is_active: bool
    is_published: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
