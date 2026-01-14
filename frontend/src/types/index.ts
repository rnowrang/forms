// Template types
export interface TemplateSchemaField {
  id: string
  type: 'text' | 'textarea' | 'checkbox' | 'radio' | 'select' | 'date' | 'email' | 'phone' | 'repeatable'
  label: string
  section_id: string
  required?: boolean
  placeholder?: string
  help_text?: string
  default_value?: any
  options?: { value: string; label: string }[]
  validation?: Record<string, any>
  anchor?: {
    type: string
    [key: string]: any
  }
  repeatable_config?: {
    min_rows?: number
    max_rows?: number
    columns?: { id: string; label: string; type: string }[]
  }
  order?: number
  // Visual grouping
  indent?: number  // Indentation level (0, 1, 2) for nested/related fields
  group_start?: string  // Start a new visual group with this label
  group_end?: boolean  // End the current visual group
  // Table layout for fixed tables
  table_group?: string  // Group ID for fields that should be rendered together in a table
  table_row?: number  // Row index in the table (0-based)
  table_col?: number  // Column index in the table (0-based)
  table_config?: {  // Only on first field of table group
    columns: { id: string; label: string }[]
    rows: { id: string; label: string }[]
  }
  // Column layout for side-by-side fields
  column_group?: string  // Group ID for fields displayed in columns
  column_index?: number  // Which column (0, 1, 2, etc.)
}

export interface TemplateSchemaSection {
  id: string
  title: string
  description?: string
  order: number
  collapsible?: boolean
  collapsed_by_default?: boolean
}

export interface TemplateSchemaRule {
  id: string
  conditions: {
    field: string
    operator: 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'is_empty' | 'is_not_empty'
    value?: any
  }[]
  then_actions: {
    action: 'show' | 'hide' | 'require' | 'optional' | 'clear' | 'set_value'
    field: string
    value?: any
  }[]
  else_actions?: {
    action: 'show' | 'hide' | 'require' | 'optional' | 'clear' | 'set_value'
    field: string
    value?: any
  }[]
}

export interface TemplateSchema {
  sections: TemplateSchemaSection[]
  fields: TemplateSchemaField[]
  rules: TemplateSchemaRule[]
}

export interface Template {
  id: number
  name: string
  description?: string
  version: string
  original_file_name: string
  schema: TemplateSchema
  is_active: boolean
  is_published: boolean
  created_at: string
  updated_at?: string
}

// Form types
export type FormStatus = 'draft' | 'in_review' | 'needs_changes' | 'approved' | 'locked'

export interface FormInstance {
  id: number
  template_id: number
  owner_id: number
  title: string
  status: FormStatus
  current_version_number: number
  created_at: string
  updated_at?: string
  submitted_at?: string
  data?: Record<string, any>
  template_name?: string
  owner_name?: string
}

export interface FormVersion {
  id: number
  form_instance_id: number
  version_number: number
  version_label?: string
  data_snapshot: Record<string, any>
  status_at_creation: FormStatus
  generated_docx_path?: string
  generated_pdf_path?: string
  created_at: string
  created_by_id: number
  created_by_name?: string
}

// Audit types
export interface ChangeEvent {
  id: number
  form_instance_id: number
  version_id?: number
  user_id: number
  user_name?: string
  field_id: string
  field_label?: string
  old_value?: any
  new_value?: any
  action_type?: string
  action_details?: string
  timestamp: string
}

// Review types
export interface Comment {
  id: number
  thread_id: number
  author_id: number
  author_name?: string
  content: string
  created_at: string
  updated_at?: string
  is_deleted: boolean
}

export interface CommentThread {
  id: number
  form_instance_id: number
  field_id?: string
  section_id?: string
  is_resolved: boolean
  resolved_at?: string
  resolved_by_id?: number
  resolved_by_name?: string
  created_at: string
  comments: Comment[]
}

export interface ReviewAction {
  id: number
  form_instance_id: number
  version_id: number
  performed_by_id: number
  performed_by_name?: string
  action_type: 'submit_for_review' | 'request_changes' | 'approve' | 'reject' | 'return_to_draft'
  notes?: string
  created_at: string
}
