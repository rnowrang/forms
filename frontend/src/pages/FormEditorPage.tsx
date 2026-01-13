import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller, useWatch } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  ArrowLeft,
  Save,
  Send,
  ChevronDown,
  ChevronRight,
  Loader2,
  History,
  Download,
  HelpCircle,
  Plus,
  Trash2,
} from 'lucide-react'
import { formsApi, templatesApi, reviewApi, versionsApi, exportApi } from '../lib/api'
import type { TemplateSchemaSection, TemplateSchemaField } from '../types'

// Simple debounce utility
function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const [timer, setTimer] = useState<ReturnType<typeof setTimeout> | null>(null)
  
  return useCallback((...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    const newTimer = setTimeout(() => callback(...args), delay)
    setTimer(newTimer)
  }, [callback, delay, timer]) as T
}

export default function FormEditorPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['sec_personnel', 'sec_study_info', 'sec_study_summary']))
  const [isSaving, setIsSaving] = useState(false)
  const [showVersionModal, setShowVersionModal] = useState(false)
  const [versionLabel, setVersionLabel] = useState('')
  // hiddenFields is now computed via useMemo as hiddenFieldsComputed

  // Fetch form data
  const { data: form, isLoading: formLoading } = useQuery({
    queryKey: ['form', id],
    queryFn: () => formsApi.get(Number(id)),
    enabled: !!id,
  })

  // Fetch template schema
  const { data: template, isLoading: templateLoading } = useQuery({
    queryKey: ['template', form?.template_id],
    queryFn: () => templatesApi.get(form!.template_id),
    enabled: !!form?.template_id,
  })

  // Form state
  const { control, setValue, getValues } = useForm({
    defaultValues: form?.data || {},
  })

  // Update form values when data loads
  useEffect(() => {
    if (form?.data) {
      Object.entries(form.data).forEach(([key, value]) => {
        setValue(key, value)
      })
    }
  }, [form?.data, setValue])

  // Watch all form values - useWatch triggers re-render on changes
  const watchedValues = useWatch({ control })

  // Helper to get nested value by dot-notation path (e.g., "personnel.has_alt_contact")
  const getNestedValue = (obj: any, path: string): any => {
    return path.split('.').reduce((curr, key) => curr?.[key], obj)
  }

  // Evaluate conditional rules - computed on every render
  const computeHiddenFields = (): Set<string> => {
    if (!template?.schema) return new Set<string>()

    const newHidden = new Set<string>()

    // First, hide fields that have visible: false by default
    const schemaFields = template.schema.fields || []
    schemaFields.forEach((field: any) => {
      if (field.visible === false) {
        newHidden.add(field.id)
      }
    })

    // Then evaluate rules (which can show hidden fields)
    if (!template.schema.rules) {
      return newHidden
    }

    template.schema.rules.forEach((rule: any) => {
      let conditionsMet = true

      for (const condition of rule.conditions || []) {
        // Use getNestedValue to properly access dot-notation paths like "personnel.has_alt_contact"
        const fieldValue = getNestedValue(watchedValues, condition.field)

        // Debug specific rules
        if (rule.id === 'rule_alt_contact' || rule.id === 'rule_funding_intramural') {
          console.log(`Rule ${rule.id}: field=${condition.field}, value=${fieldValue}, expected=${condition.value}`)
        }

        switch (condition.operator) {
          case 'equals':
            conditionsMet = conditionsMet && fieldValue === condition.value
            break
          case 'not_equals':
            conditionsMet = conditionsMet && fieldValue !== condition.value
            break
          case 'contains':
            if (Array.isArray(fieldValue)) {
              conditionsMet = conditionsMet && fieldValue.includes(condition.value)
            } else if (typeof fieldValue === 'string') {
              conditionsMet = conditionsMet && fieldValue.toLowerCase().includes(condition.value.toLowerCase())
            } else {
              conditionsMet = false
            }
            break
          case 'is_empty':
            conditionsMet = conditionsMet && (!fieldValue || fieldValue === '' || (Array.isArray(fieldValue) && fieldValue.length === 0))
            break
          case 'is_not_empty':
          case 'not_empty':
            conditionsMet = conditionsMet && fieldValue && fieldValue !== '' && (!Array.isArray(fieldValue) || fieldValue.length > 0)
            break
        }
      }

      const actions = conditionsMet ? rule.then_actions : rule.else_actions

      actions?.forEach((action: any) => {
        if (action.action === 'hide') {
          newHidden.add(action.field)
        } else if (action.action === 'show') {
          newHidden.delete(action.field)
        }
      })
    })

    return newHidden
  }

  const hiddenFieldsComputed = computeHiddenFields()

  // Autosave mutation
  const saveMutation = useMutation({
    mutationFn: (changes: any[]) => formsApi.updateData(Number(id), changes),
    onSuccess: () => {
      setIsSaving(false)
    },
    onError: () => {
      toast.error('Failed to save changes')
      setIsSaving(false)
    },
  })

  // Debounced save
  const debouncedSave = useDebouncedCallback((fieldId: string, oldValue: any, newValue: any, label?: string) => {
    setIsSaving(true)
    saveMutation.mutate([{
      field_id: fieldId,
      field_label: label,
      old_value: oldValue,
      new_value: newValue,
    }])
  }, 1000)

  // Handle field change
  const handleFieldChange = (fieldId: string, value: any, label?: string) => {
    const oldValue = getValues(fieldId)
    setValue(fieldId, value)
    debouncedSave(fieldId, oldValue, value, label)
  }

  // Create version
  const createVersionMutation = useMutation({
    mutationFn: () => versionsApi.create(Number(id), versionLabel || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form', id] })
      toast.success('Version created')
      setShowVersionModal(false)
      setVersionLabel('')
    },
    onError: () => {
      toast.error('Failed to create version')
    },
  })

  // Submit for review
  const submitMutation = useMutation({
    mutationFn: () => reviewApi.submitForReview(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form', id] })
      toast.success('Form submitted for review')
      navigate(`/forms/${id}`)
    },
    onError: () => {
      toast.error('Failed to submit for review')
    },
  })

  // Export
  const handleExport = async (format: 'docx' | 'pdf') => {
    try {
      toast.loading('Generating document...')
      const blob = format === 'docx' 
        ? await exportApi.downloadDocx(Number(id))
        : await exportApi.downloadPdf(Number(id))
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${form?.title || 'form'}.${format}`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.dismiss()
      toast.success('Document downloaded')
    } catch {
      toast.dismiss()
      toast.error('Failed to generate document')
    }
  }

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  if (formLoading || templateLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
      </div>
    )
  }

  if (!form || !template) {
    return (
      <div className="text-center py-12">
        <p className="text-surface-500">Form not found</p>
      </div>
    )
  }

  const sections = template.schema?.sections || []
  const fields = template.schema?.fields || []

  const getFieldsForSection = (sectionId: string) =>
    fields
      .filter((f: TemplateSchemaField) => f.section_id === sectionId && !hiddenFieldsComputed.has(f.id))
      .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-surface-900">{form.title}</h1>
              {isSaving && (
                <span className="flex items-center gap-1 text-xs text-surface-500">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Saving...
                </span>
              )}
            </div>
            <p className="text-sm text-surface-500">
              {template.name} • v{form.current_version_number}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowVersionModal(true)}
            className="btn-ghost"
          >
            <History className="w-4 h-4" />
            Save Version
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="btn-ghost"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending}
            className="btn-primary"
          >
            {submitMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Submit for Review
          </button>
        </div>
      </div>

      {/* Form sections */}
      <div className="space-y-4">
        {sections
          .sort((a: any, b: any) => a.order - b.order)
          .map((section: TemplateSchemaSection) => {
            const sectionFields = getFieldsForSection(section.id)
            const isExpanded = expandedSections.has(section.id)
            
            if (sectionFields.length === 0) return null
            
            return (
              <div key={section.id} className="form-section">
                <button
                  onClick={() => toggleSection(section.id)}
                  className="section-header"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-surface-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-surface-400" />
                    )}
                    <span className="font-medium text-surface-900">{section.title}</span>
                  </div>
                  <span className="text-sm text-surface-500">
                    {sectionFields.length} field{sectionFields.length !== 1 ? 's' : ''}
                  </span>
                </button>
                
                {isExpanded && (
                  <div className="form-section-content space-y-6">
                    {sectionFields.map((field: TemplateSchemaField, index: number) => {
                      const indent = field.indent || 0
                      const showGroupStart = field.group_start
                      const showGroupEnd = field.group_end ||
                        (index < sectionFields.length - 1 && sectionFields[index + 1].group_start)

                      return (
                        <div key={field.id}>
                          {/* Group header */}
                          {showGroupStart && (
                            <div className="text-sm font-medium text-surface-600 mb-3 mt-2 pb-1 border-b border-surface-200">
                              {field.group_start}
                            </div>
                          )}

                          {/* Field with indentation */}
                          <div
                            className={`
                              ${indent > 0 ? 'ml-6 pl-4 border-l-2 border-surface-200' : ''}
                              ${indent > 1 ? 'ml-12' : ''}
                            `}
                          >
                            <FormField
                              field={field}
                              control={control}
                              onChange={(value) => handleFieldChange(field.id, value, field.label)}
                            />
                          </div>

                          {/* Group end spacing */}
                          {showGroupEnd && (
                            <div className="mt-4 mb-2" />
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
      </div>

      {/* Version Modal */}
      {showVersionModal && (
        <div className="fixed inset-0 bg-surface-900/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md animate-slide-up">
            <div className="p-6 border-b border-surface-100">
              <h3 className="text-lg font-semibold text-surface-900">Save Version</h3>
              <p className="text-sm text-surface-500 mt-1">Create a named snapshot of your current progress</p>
            </div>
            <div className="p-6">
              <label className="label">Version Label (optional)</label>
              <input
                type="text"
                value={versionLabel}
                onChange={(e) => setVersionLabel(e.target.value)}
                className="input"
                placeholder="e.g., Draft before adding personnel"
              />
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-surface-100">
              <button onClick={() => setShowVersionModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={() => createVersionMutation.mutate()}
                disabled={createVersionMutation.isPending}
                className="btn-primary"
              >
                {createVersionMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Save Version
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Field component
function FormField({
  field,
  control,
  onChange,
}: {
  field: TemplateSchemaField
  control: any
  onChange: (value: any) => void
}) {
  const renderField = () => {
    switch (field.type) {
      case 'text':
      case 'email':
      case 'phone':
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => (
              <input
                type={field.type === 'email' ? 'email' : field.type === 'phone' ? 'tel' : 'text'}
                value={value || ''}
                onChange={(e) => {
                  formOnChange(e.target.value)
                  onChange(e.target.value)
                }}
                placeholder={field.placeholder}
                className="input"
              />
            )}
          />
        )
      
      case 'textarea':
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => (
              <textarea
                value={value || ''}
                onChange={(e) => {
                  formOnChange(e.target.value)
                  onChange(e.target.value)
                }}
                placeholder={field.placeholder}
                rows={4}
                className="input resize-y"
              />
            )}
          />
        )
      
      case 'date':
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => (
              <input
                type="date"
                value={value || ''}
                onChange={(e) => {
                  formOnChange(e.target.value)
                  onChange(e.target.value)
                }}
                className="input"
              />
            )}
          />
        )
      
      case 'select':
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => (
              <select
                value={value || ''}
                onChange={(e) => {
                  formOnChange(e.target.value)
                  onChange(e.target.value)
                }}
                className="input"
              >
                <option value="">Select an option...</option>
                {field.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            )}
          />
        )
      
      case 'radio':
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => (
              <div className="space-y-2">
                {field.options?.map((opt) => (
                  <label key={opt.value} className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name={field.id}
                      value={opt.value}
                      checked={value === opt.value}
                      onChange={(e) => {
                        formOnChange(e.target.value)
                        onChange(e.target.value)
                      }}
                      className="w-4 h-4 text-primary-600"
                    />
                    <span className="text-surface-700">{opt.label}</span>
                  </label>
                ))}
              </div>
            )}
          />
        )
      
      case 'checkbox':
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => {
              const selectedValues = Array.isArray(value) ? value : []
              return (
                <div className="space-y-2">
                  {field.options?.map((opt) => (
                    <label key={opt.value} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        value={opt.value}
                        checked={selectedValues.includes(opt.value)}
                        onChange={(e) => {
                          const newValue = e.target.checked
                            ? [...selectedValues, opt.value]
                            : selectedValues.filter((v: string) => v !== opt.value)
                          formOnChange(newValue)
                          onChange(newValue)
                        }}
                        className="w-4 h-4 text-primary-600 rounded"
                      />
                      <span className="text-surface-700">{opt.label}</span>
                    </label>
                  ))}
                </div>
              )
            }}
          />
        )
      
      case 'repeatable':
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => {
              const rows = Array.isArray(value) ? value : []
              const config = field.repeatable_config || { columns: [], max_rows: 10 }
              const columns = config.columns || []

              const addRow = () => {
                if (rows.length < (config.max_rows || 10)) {
                  const newRow: Record<string, string> = {}
                  columns.forEach((col: any) => {
                    newRow[col.id] = ''
                  })
                  const newRows = [...rows, newRow]
                  formOnChange(newRows)
                  onChange(newRows)
                }
              }

              const removeRow = (index: number) => {
                const newRows = rows.filter((_: any, i: number) => i !== index)
                formOnChange(newRows)
                onChange(newRows)
              }

              const updateCell = (rowIndex: number, colId: string, cellValue: string) => {
                const newRows = rows.map((row: any, i: number) =>
                  i === rowIndex ? { ...row, [colId]: cellValue } : row
                )
                formOnChange(newRows)
                onChange(newRows)
              }

              return (
                <div className="space-y-3">
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="bg-surface-50">
                          {columns.map((col: any) => (
                            <th key={col.id} className="px-3 py-2 text-left text-sm font-medium text-surface-700 border border-surface-200">
                              {col.label}
                            </th>
                          ))}
                          <th className="px-3 py-2 w-10 border border-surface-200"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((row: any, rowIndex: number) => (
                          <tr key={rowIndex}>
                            {columns.map((col: any) => (
                              <td key={col.id} className="border border-surface-200 p-1">
                                <input
                                  type={col.type === 'email' ? 'email' : 'text'}
                                  value={row[col.id] || ''}
                                  onChange={(e) => updateCell(rowIndex, col.id, e.target.value)}
                                  className="w-full px-2 py-1 text-sm border-0 focus:ring-1 focus:ring-primary-500 rounded"
                                  placeholder={col.label}
                                />
                              </td>
                            ))}
                            <td className="border border-surface-200 p-1 text-center">
                              <button
                                type="button"
                                onClick={() => removeRow(rowIndex)}
                                className="text-surface-400 hover:text-accent-rose p-1"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                        {rows.length === 0 && (
                          <tr>
                            <td colSpan={columns.length + 1} className="border border-surface-200 px-3 py-4 text-center text-surface-500 text-sm">
                              No rows added yet
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  {rows.length < (config.max_rows || 10) && (
                    <button
                      type="button"
                      onClick={addRow}
                      className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
                    >
                      <Plus className="w-4 h-4" />
                      {(config as any).add_button_text || 'Add Row'}
                    </button>
                  )}
                </div>
              )
            }}
          />
        )

      default:
        return (
          <Controller
            name={field.id}
            control={control}
            render={({ field: { value, onChange: formOnChange } }) => (
              <input
                type="text"
                value={value || ''}
                onChange={(e) => {
                  formOnChange(e.target.value)
                  onChange(e.target.value)
                }}
                className="input"
              />
            )}
          />
        )
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <label className="label mb-0">
          {field.label}
          {field.required && <span className="text-accent-rose ml-1">*</span>}
        </label>
        {field.help_text && (
          <button className="text-surface-400 hover:text-surface-600" title={field.help_text}>
            <HelpCircle className="w-4 h-4" />
          </button>
        )}
      </div>
      {renderField()}
    </div>
  )
}
